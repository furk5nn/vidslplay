package dev.localvideo.screens.client;

import net.minecraft.client.Minecraft;
import net.minecraft.network.chat.Component;

import java.io.File;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
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
        if (lower.endsWith(".webm") || isImage(lower)) {
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
                    Path ffmpeg = ensureFfmpeg(cacheDir);
                    Path temp = cacheDir.resolve(hash + ".part.webm");
                    Files.deleteIfExists(temp);

                    transcode(ffmpeg, source.toPath(), temp);
                    if (!Files.isRegularFile(temp) || Files.size(temp) == 0) {
                        throw new IllegalStateException("FFmpeg çıktı üretmedi");
                    }

                    Files.move(temp, cached, StandardCopyOption.REPLACE_EXISTING);
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

    private static Path ensureFfmpeg(Path cacheDir) throws Exception {
        Path binDir = cacheDir.resolve("bin");
        Files.createDirectories(binDir);
        Path exe = binDir.resolve("ffmpeg.exe");

        if (Files.isRegularFile(exe) && Files.size(exe) > 1_000_000) {
            return exe;
        }

        try (InputStream in = VideoCompatibilityCache.class
                .getResourceAsStream("/localvideoscreens/ffmpeg/ffmpeg.exe")) {
            if (in == null) {
                throw new IllegalStateException("Gömülü ffmpeg.exe bulunamadı");
            }
            Path tmp = binDir.resolve("ffmpeg.exe.part");
            Files.copy(in, tmp, StandardCopyOption.REPLACE_EXISTING);
            Files.move(tmp, exe, StandardCopyOption.REPLACE_EXISTING);
        }

        return exe;
    }

    private static void transcode(Path ffmpeg, Path source, Path destination) throws Exception {
        ProcessBuilder pb = new ProcessBuilder(
                ffmpeg.toAbsolutePath().toString(),
                "-y",
                "-hide_banner",
                "-loglevel", "error",
                "-threads", "4",
                "-filter_threads", "4",
                "-i", source.toAbsolutePath().toString(),
                "-map", "0:v:0",
                "-map", "0:a:0?",
                "-vf", "scale=1280:720:force_original_aspect_ratio=decrease",
                "-c:v", "libvpx-vp9",
                "-deadline", "realtime",
                "-cpu-used", "8",
                "-row-mt", "1",
                "-threads", "4",
                "-b:v", "2200k",
                "-maxrate", "3500k",
                "-bufsize", "5000k",
                "-c:a", "libopus",
                "-b:a", "128k",
                "-f", "webm",
                destination.toAbsolutePath().toString()
        );
        pb.redirectErrorStream(true);

        Process process = pb.start();
        String output;
        try (InputStream in = process.getInputStream()) {
            output = new String(in.readAllBytes(), StandardCharsets.UTF_8);
        }
        int exit = process.waitFor();
        if (exit != 0) {
            throw new IllegalStateException("FFmpeg exit=" + exit + " " + output);
        }
    }

    private static boolean isImage(String lowerName) {
        return lowerName.endsWith(".jpg")
                || lowerName.endsWith(".jpeg")
                || lowerName.endsWith(".png")
                || lowerName.endsWith(".gif")
                || lowerName.endsWith(".webp")
                || lowerName.endsWith(".bmp");
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
