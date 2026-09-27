package com.furk5nn.videoscreen.client;

import java.io.File;
import net.minecraft.client.Minecraft;
import net.minecraft.resources.Identifier;
import org.watermedia.api.media.MRL;
import org.watermedia.api.media.MediaAPI;
import org.watermedia.api.media.players.MediaPlayer;

public final class WaterMediaVideoPlayer implements AutoCloseable {
    private static int NEXT_ID;

    private final File source;
    private final Identifier textureId = Identifier.fromNamespaceAndPath("videoscreen", "watermedia/video_" + NEXT_ID++);
    private MRL mrl;
    private MediaPlayer player;
    private ExternalGlTexture wrappedTexture;
    private long wrappedNativeId = -1L;
    private boolean paused;
    private String error;

    public WaterMediaVideoPlayer(File source) {
        this.source = source.getAbsoluteFile();
        this.mrl = MediaAPI.mrl(this.source.getAbsolutePath());
    }

    public void tickInit() {
        if (player != null || error != null) return;
        if (mrl == null) {
            error = "WATERMeDIA failed to create media reference";
            return;
        }

        if (mrl.status() == MRL.Status.FETCHING) return;
        if (mrl.status() == MRL.Status.ERROR) {
            error = "WATERMeDIA could not read this file";
            return;
        }

        try {
            Minecraft mc = Minecraft.getInstance();
            Thread renderThread = Thread.currentThread();
            player = MediaAPI.createPlayer(
                mrl,
                () -> MediaAPI.glEngine(renderThread, task -> mc.execute(task)),
                MediaAPI::alEngine
            );

            if (player == null) return;

            player.repeat(true);
            player.volume(100);
            if (!player.start()) {
                // Some backends report false when the request is queued; do not fail eagerly.
            }
        } catch (Throwable t) {
            t.printStackTrace();
            error = "WATERMeDIA player error: " + t.getClass().getSimpleName();
            if (player != null) {
                try { player.release(); } catch (Throwable ignored) {}
                player = null;
            }
        }
    }

    public boolean isReady() {
        tickInit();
        if (player == null || !player.canPlay() || player.texture() <= 0) return false;
        ensureTextureRegistered();
        return wrappedTexture != null;
    }

    public Identifier texture() {
        return wrappedTexture == null ? null : textureId;
    }

    public String error() {
        return error;
    }

    public void togglePause() {
        if (player == null) return;
        paused = !paused;
        player.pause(paused);
    }

    public boolean isPaused() {
        return paused;
    }

    public File source() {
        return source;
    }

    private void ensureTextureRegistered() {
        long nativeId = player.texture();
        if (nativeId <= 0 || nativeId > Integer.MAX_VALUE) return;
        if (wrappedTexture != null && wrappedNativeId == nativeId) return;

        Minecraft mc = Minecraft.getInstance();
        if (wrappedTexture != null) {
            mc.getTextureManager().release(textureId);
            wrappedTexture = null;
        }

        wrappedNativeId = nativeId;
        wrappedTexture = new ExternalGlTexture((int) nativeId, Math.max(1, player.width()), Math.max(1, player.height()));
        mc.getTextureManager().register(textureId, wrappedTexture);
    }

    @Override
    public void close() {
        Minecraft mc = Minecraft.getInstance();
        if (wrappedTexture != null) {
            mc.getTextureManager().release(textureId);
            wrappedTexture = null;
        }
        if (player != null) {
            try { player.release(); } catch (Throwable ignored) {}
            player = null;
        }
    }
}
