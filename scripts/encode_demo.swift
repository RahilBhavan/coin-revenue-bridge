import AVFoundation
import CoreGraphics
import CoreVideo
import Foundation
import ImageIO

let arguments = CommandLine.arguments
guard arguments.count == 3 else {
    fputs("usage: swift encode_demo.swift FRAME_DIR OUTPUT_MP4\n", stderr)
    exit(2)
}

let frameDirectory = URL(fileURLWithPath: arguments[1], isDirectory: true)
let outputURL = URL(fileURLWithPath: arguments[2])
let durations = [15, 23, 27, 27, 33, 23, 21, 11]
let width = 1280
let height = 720

try? FileManager.default.removeItem(at: outputURL)
let writer = try AVAssetWriter(outputURL: outputURL, fileType: .mp4)
let settings: [String: Any] = [
    AVVideoCodecKey: AVVideoCodecType.h264,
    AVVideoWidthKey: width,
    AVVideoHeightKey: height,
    AVVideoCompressionPropertiesKey: [AVVideoAverageBitRateKey: 900_000]
]
let input = AVAssetWriterInput(mediaType: .video, outputSettings: settings)
input.expectsMediaDataInRealTime = false
let attributes: [String: Any] = [
    kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32ARGB,
    kCVPixelBufferWidthKey as String: width,
    kCVPixelBufferHeightKey as String: height
]
let adaptor = AVAssetWriterInputPixelBufferAdaptor(assetWriterInput: input, sourcePixelBufferAttributes: attributes)
guard writer.canAdd(input) else { fatalError("cannot add video input") }
writer.add(input)
guard writer.startWriting() else { fatalError(writer.error?.localizedDescription ?? "startWriting failed") }
writer.startSession(atSourceTime: .zero)

func pixelBuffer(for url: URL) -> CVPixelBuffer {
    guard let source = CGImageSourceCreateWithURL(url as CFURL, nil),
          let image = CGImageSourceCreateImageAtIndex(source, 0, nil) else { fatalError("cannot read \(url.path)") }
    var maybe: CVPixelBuffer?
    let result = CVPixelBufferCreate(kCFAllocatorDefault, width, height, kCVPixelFormatType_32ARGB, attributes as CFDictionary, &maybe)
    guard result == kCVReturnSuccess, let buffer = maybe else { fatalError("cannot create pixel buffer") }
    CVPixelBufferLockBaseAddress(buffer, [])
    defer { CVPixelBufferUnlockBaseAddress(buffer, []) }
    guard let context = CGContext(data: CVPixelBufferGetBaseAddress(buffer), width: width, height: height,
                                  bitsPerComponent: 8, bytesPerRow: CVPixelBufferGetBytesPerRow(buffer),
                                  space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGImageAlphaInfo.noneSkipFirst.rawValue)
    else { fatalError("cannot create context") }
    context.translateBy(x: 0, y: CGFloat(height)); context.scaleBy(x: 1, y: -1)
    context.draw(image, in: CGRect(x: 0, y: 0, width: width, height: height))
    return buffer
}

var second: Int64 = 0
for index in 0..<durations.count {
    let url = frameDirectory.appendingPathComponent(String(format: "slide-%02d.png", index + 1))
    let buffer = pixelBuffer(for: url)
    for _ in 0..<durations[index] {
        while !input.isReadyForMoreMediaData { Thread.sleep(forTimeInterval: 0.01) }
        guard adaptor.append(buffer, withPresentationTime: CMTime(value: second, timescale: 1)) else {
            fatalError(writer.error?.localizedDescription ?? "append failed")
        }
        second += 1
    }
}
input.markAsFinished()
let semaphore = DispatchSemaphore(value: 0)
writer.finishWriting { semaphore.signal() }
semaphore.wait()
guard writer.status == .completed else { fatalError(writer.error?.localizedDescription ?? "encoding failed") }
print("encoded \(second)s to \(outputURL.path)")
