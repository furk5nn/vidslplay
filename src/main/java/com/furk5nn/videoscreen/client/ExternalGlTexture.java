package com.furk5nn.videoscreen.client;

import com.mojang.blaze3d.opengl.GlTexture;
import com.mojang.blaze3d.textures.TextureFormat;
import net.minecraft.client.renderer.texture.AbstractTexture;

final class ExternalGlTexture extends AbstractTexture {
    ExternalGlTexture(int textureId, int width, int height) {
        this.defaultBlur = false;
        this.texture = new DirectGlTexture(textureId, Math.max(1, width), Math.max(1, height));
    }

    @Override
    public void close() {
        // WATERMeDIA owns the OpenGL texture. Minecraft must not delete it.
        this.texture = null;
    }

    private static final class DirectGlTexture extends GlTexture {
        private final int width;
        private final int height;

        private DirectGlTexture(int textureId, int width, int height) {
            super("VideoScreen WATERMeDIA Texture", TextureFormat.RGBA8, width, height, 1, textureId);
            this.width = width;
            this.height = height;
            this.closed = false;
        }

        @Override
        public void close() {
            // Do not glDeleteTexture here. WATERMeDIA owns it.
            this.closed = true;
        }

        @Override
        public int getWidth(int mipLevel) {
            return Math.max(1, width >> mipLevel);
        }

        @Override
        public int getHeight(int mipLevel) {
            return Math.max(1, height >> mipLevel);
        }
    }
}
