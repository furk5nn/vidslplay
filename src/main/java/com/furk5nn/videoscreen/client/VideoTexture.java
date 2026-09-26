package com.furk5nn.videoscreen.client;

import com.mojang.blaze3d.platform.NativeImage;
import java.nio.ByteBuffer;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.texture.DynamicTexture;
import net.minecraft.resources.Identifier;
import org.lwjgl.system.MemoryUtil;

public final class VideoTexture implements AutoCloseable {
    private static int NEXT_ID;
    private final Identifier id = Identifier.fromNamespaceAndPath("videoscreen", "dynamic/video_" + NEXT_ID++);
    private ByteBuffer staging;
    private DynamicTexture texture;
    private int width;
    private int height;
    private boolean dirty;

    public Identifier id() { return id; }

    public synchronized void submit(byte[] rgba, int width, int height) {
        int size = width * height * 4;
        if (rgba.length < size) return;
        if (staging == null || this.width != width || this.height != height) {
            if (staging != null) MemoryUtil.memFree(staging);
            staging = MemoryUtil.memAlloc(size);
            this.width = width;
            this.height = height;
            dirty = true;
        }
        staging.clear();
        staging.put(rgba, 0, size);
        staging.flip();
        dirty = true;
    }

    public synchronized boolean uploadIfDirty() {
        if (staging == null || width <= 0 || height <= 0) return false;
        if (texture == null || texture.getPixels() == null
                || texture.getPixels().getWidth() != width || texture.getPixels().getHeight() != height) {
            if (texture != null) Minecraft.getInstance().getTextureManager().release(id);
            texture = new DynamicTexture(() -> id.toString(), width, height, true);
            Minecraft.getInstance().getTextureManager().register(id, texture);
        }
        if (!dirty) return true;
        NativeImage image = texture.getPixels();
        if (image == null) return false;
        staging.rewind();
        MemoryUtil.memCopy(MemoryUtil.memAddress(staging), image.getPointer(), (long)width * height * 4L);
        texture.upload();
        dirty = false;
        return true;
    }

    @Override
    public synchronized void close() {
        if (staging != null) {
            MemoryUtil.memFree(staging);
            staging = null;
        }
        if (texture != null) {
            Minecraft.getInstance().getTextureManager().release(id);
            texture = null;
        }
    }
}
