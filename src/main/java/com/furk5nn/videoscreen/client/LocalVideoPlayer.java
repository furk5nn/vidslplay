package com.furk5nn.videoscreen.client;

import java.awt.image.BufferedImage;
import java.io.File;
import java.util.concurrent.atomic.AtomicBoolean;
import org.jcodec.api.FrameGrab;
import org.jcodec.scale.AWTUtil;
import org.jcodec.common.io.NIOUtils;
import org.jcodec.common.model.Picture;

public final class LocalVideoPlayer implements AutoCloseable {
    private final File file;
    private final VideoTexture texture = new VideoTexture();
    private final AtomicBoolean running = new AtomicBoolean(true);
    private volatile boolean paused;
    private volatile boolean loop = true;
    private Thread worker;

    public LocalVideoPlayer(File file) {
        this.file = file;
        start();
    }

    public VideoTexture texture() { return texture; }
    public boolean isPaused() { return paused; }
    public boolean isLoop() { return loop; }
    public void togglePause() { paused = !paused; }
    public void toggleLoop() { loop = !loop; }

    private void start() {
        worker = Thread.ofVirtual().name("videoscreen-decoder").start(() -> {
            while (running.get()) {
                try {
                    decodeOnce();
                    if (!loop) {
                        paused = true;
                        return;
                    }
                } catch (Throwable t) {
                    t.printStackTrace();
                    return;
                }
            }
        });
    }

    private void decodeOnce() throws Exception {
        FrameGrab grab = FrameGrab.createFrameGrab(NIOUtils.readableChannel(file));
        long frameNanos = 1_000_000_000L / 30L;
        while (running.get()) {
            if (paused) {
                Thread.sleep(25);
                continue;
            }
            long started = System.nanoTime();
            Picture picture = grab.getNativeFrame();
            if (picture == null) break;
            BufferedImage image = AWTUtil.toBufferedImage(picture);
            texture.submit(toRgba(image), image.getWidth(), image.getHeight());
            long sleep = frameNanos - (System.nanoTime() - started);
            if (sleep > 0) Thread.sleep(sleep / 1_000_000L, (int)(sleep % 1_000_000L));
        }
    }

    private static byte[] toRgba(BufferedImage image) {
        int w = image.getWidth();
        int h = image.getHeight();
        int[] argb = image.getRGB(0, 0, w, h, null, 0, w);
        byte[] out = new byte[w * h * 4];
        int p = 0;
        for (int c : argb) {
            out[p++] = (byte)((c >> 16) & 0xFF);
            out[p++] = (byte)((c >> 8) & 0xFF);
            out[p++] = (byte)(c & 0xFF);
            out[p++] = (byte)((c >> 24) & 0xFF);
        }
        return out;
    }

    @Override
    public void close() {
        running.set(false);
        if (worker != null) worker.interrupt();
        texture.close();
    }
}
