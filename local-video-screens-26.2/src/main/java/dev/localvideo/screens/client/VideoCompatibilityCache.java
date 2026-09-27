package dev.localvideo.screens.client;

import net.minecraft.client.Minecraft;
import net.minecraft.network.chat.Component;
import org.bytedeco.ffmpeg.global.avcodec;
import org.bytedeco.javacv.FFmpegFrameGrabber;
import org.bytedeco.javacv.FFmpegFrameRecorder;
import org.bytedeco.javacv.Frame;

import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.function.Consumer;

final class VideoCompatibilityCache {
    private static final ExecutorService TRANSCODER = Executors.newSingleThreadExecutor(r -> {
        Thread t = new Thread(r, "LocalVideoScreens-Transcoder");
        t.setDaemon(true);
        t.setPriority(Thread.NORM_PRIORITY - 1);
        return t;
    });

    private VideoCompatibilityCache() {}

    static void prepare(File source, Consumer<File> callback) {
        if (source == null || !source.isFile()) {
            Minecraft.getInstance().execute(() -> callback.accept(null));
            return;
        }

        String lower = source.getName().toLowerCase(Locale.ROOT);
        if (lower.endsWith(".webm")) {
            Minecraft.getInstance().execute(() -> callback.accept(source));
            return;
        }

        TRANSCODER.execute(() -> {
            File result = null;
            try {
                Path cacheDir = Minecraft.getInstance().gameDirectory.toPath()
                        .resolve("localvideoscreens-cache");
                Files.createDirectories(cacheDir);

                String fingerprint = source.getCanonicalPath() + "|" + source.length() + "|" + source.lastModified();
                String hash = sha256(fingerprint).substring(0, 24);
                Path cached = cacheDir.resolve(hash + ".webm");

                if (Files.isRegularFile(cached) && Files.size(cached) > 0) {
                    result = cached.toFile();
                } else {
                    notifyPlayer("Video hazırlanıyor: " + source.getName());
                    Path temp = cacheDir.resolve(hash + ".part.webm");
                    Files.deleteIfExists(temp);
                    transcode(source, temp.toFile());
                    Files.move(temp, cached);
                    result = cached.toFile();
                    notifyPlayer("Video hazır.");
                }
            } catch (Throwable t) {
                t.printStackTrace();
                notifyPlayer("Video dönüştürülemedi: " + t.getClass().getSimpleName());
            }

            File finalResult = result;
            Minecraft.getInstance().execute(() -> callback.accept(finalResult));
        });
    }

    private static void transcode(File source, File destination) throws Exception {
        try (FFmpegFrameGrabber grabber = new FFmpegFrameGrabber(source)) {
            grabber.start();

            int width = even(Math.max(2, grabber.getImageWidth()));
            int height = even(Math.max(2, grabber.getImageHeight()));
            double sourceFps = grabber.getVideoFrameRate();
            double fps = sourceFps > 0 ? Math.min(30.0, sourceFps) : 30.0;

            try (FFmpegFrameRecorder recorder = new FFmpegFrameRecorder(
                    destination,
                    width,
                    height,
                    Math.max(0, grabber.getAudioChannels())
            )) {
                recorder.setFormat("webm");
                recorder.setVideoCodec(avcodec.AV_CODEC_ID_VP9);
                recorder.setAudioCodec(avcodec.AV_CODEC_ID_OPUS);
                recorder.setFrameRate(fps);
                recorder.setVideoBitrate(2_500_000);
                recorder.setAudioBitrate(128_000);
                if (grabber.getSampleRate() > 0) {
                    recorder.setSampleRate(grabber.getSampleRate());
                }

                // Keep conversion bounded. This is a one-time compatibility cache,
                // not the playback/render loop.
                recorder.setVideoOption("threads", "2");
                recorder.setAudioOption("threads", "1");
                recorder.setVideoOption("deadline", "realtime");
                recorder.setVideoOption("cpu-used", "6");
                recorder.start();

                Frame frame;
                while ((frame = grabber.grab()) != null) {
                    recorder.record(frame);
                }

                recorder.stop();
            }

            grabber.stop();
        }
    }

    private static int even(int value) {
        return (value & 1) == 0 ? value : value - 1;
    }

    private static String sha256(String value) throws Exception {
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        return HexFormat.of().formatHex(digest.digest(value.getBytes(StandardCharsets.UTF_8)));
    }

    private static void notifyPlayer(String message) {
        Minecraft.getInstance().execute(() -> {
            if (Minecraft.getInstance().player != null) {
                Minecraft.getInstance().player.sendSystemMessage(Component.literal("[Video Screen] " + message));
            }
        });
    }
}
