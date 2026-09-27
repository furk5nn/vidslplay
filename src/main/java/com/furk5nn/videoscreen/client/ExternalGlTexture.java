package com.furk5nn.videoscreen.client;

import com.mojang.blaze3d.GpuFormat;
import com.mojang.blaze3d.opengl.FrameBufferCache;
import com.mojang.blaze3d.opengl.GlTexture;
import com.mojang.blaze3d.systems.RenderSystem;
import com.mojang.blaze3d.textures.FilterMode;
import com.mojang.blaze3d.textures.GpuTexture;
import net.minecraft.client.renderer.texture.AbstractTexture;

/**
 * Non-owning Minecraft wrapper around a WATERMeDIA OpenGL texture.
 * Closing this wrapper never deletes WATERMeDIA's native GL texture.
 */
final class ExternalGlTexture extends AbstractTexture {
    private static final FrameBufferCache FRAME_BUFFER_CACHE = new FrameBufferCache();

    ExternalGlTexture(int textureId, int width, int height) {
        ForeignGlTexture foreign = new ForeignGlTexture(textureId, Math.max(1, width), Math.max(1, height));
        this.texture = foreign;
        this.textureView = RenderSystem.getDevice().createTextureView(foreign);
        this.sampler = RenderSystem.getSamplerCache().getClampToEdge(FilterMode.LINEAR);
    }

    @Override
    public void close() {
        var oldView = this.textureView;
        var oldTexture = this.texture;
        this.textureView = null;
        this.texture = null;
        this.sampler = null;

        if (oldView != null) {
            try { oldView.close(); } catch (Throwable ignored) {}
        }
        if (oldTexture != null) {
            try { oldTexture.close(); } catch (Throwable ignored) {}
        }
    }

    private static final class ForeignGlTexture extends GlTexture {
        private boolean disposed;

        private ForeignGlTexture(int glId, int width, int height) {
            super(
                GpuTexture.USAGE_TEXTURE_BINDING,
                "videoscreen-watermedia-video",
                GpuFormat.RGBA8_UNORM,
                width,
                height,
                1,
                1,
                glId,
                FRAME_BUFFER_CACHE
            );
        }

        @Override
        public void close() {
            // WATERMeDIA owns glId, so we only mark this wrapper disposed.
            disposed = true;
        }

        @Override
        public boolean isClosed() {
            return disposed;
        }
    }
}
