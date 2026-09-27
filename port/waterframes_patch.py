from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "upstream" / "waterframes"
DST = ROOT / "build-port" / "waterframes"

if DST.exists():
    shutil.rmtree(DST)
shutil.copytree(SRC, DST)

(DST / "settings.gradle").write_text('rootProject.name = "waterframes-26.2-port"\n', encoding="utf-8")

(DST / "gradle.properties").write_text("""org.gradle.jvmargs=-Xmx4G
org.gradle.daemon=false
systemProp.file.encoding=utf-8
""", encoding="utf-8")

(DST / "build.gradle").write_text("""plugins {
    id 'java'
    id 'net.neoforged.moddev' version '2.0.147'
}

version = '2.1.22-26.2-port.1'
group = 'me.srrrapero720'

base {
    archivesName = 'waterframes-NEOFORGE-mc26.2'
}

java.toolchain.languageVersion = JavaLanguageVersion.of(25)

repositories {
    mavenCentral()
    maven { url = 'https://jitpack.io' }
    maven {
        url = 'https://www.cursemaven.com'
        content { includeGroup 'curse.maven' }
    }
}

dependencies {
    implementation 'com.github.WaterMediaTeam:watermedia:2.1.37'
    implementation 'curse.maven:creativecore-257814:8285385'
}

neoForge {
    version = '26.2.0.87'

    runs {
        client { client() }
        server { server() }
    }

    mods {
        waterframes {
            sourceSet sourceSets.main
        }
    }
}

tasks.withType(JavaCompile).configureEach {
    options.encoding = 'UTF-8'
}

jar {
    manifest {
        attributes(
            'Specification-Title': 'waterframes',
            'Specification-Vendor': 'SrRapero720',
            'Specification-Version': '1',
            'Implementation-Title': 'WaterFrames 26.2 Port',
            'Implementation-Version': project.version,
            'Implementation-Vendor': 'SrRapero720 / 26.2 compatibility port'
        )
    }
}
""", encoding="utf-8")

# 26.2 does not currently have a compatible WATERViSION release.
wv = DST / "src/main/java/me/srrapero720/waterframes/common/compat/watervision/WVCompat.java"
wv.write_text("""package me.srrapero720.waterframes.common.compat.watervision;

import java.net.URI;

public final class WVCompat {
    private WVCompat() {}

    public static boolean installed() {
        return false;
    }

    public static void openScreen(URI uri, int volume) {
        // WATERViSION integration is optional and unavailable on 26.2.
    }
}
""", encoding="utf-8")

meta = DST / "src/main/resources/META-INF/neoforge.mods.toml"
meta.write_text("""modLoader="javafml"
loaderVersion="[4,)"
license="All-Rights-Reserved"
issueTrackerURL="https://github.com/SrRapero720/waterframes/issues"
logoFile="pack.png"

[[mods]]
modId="waterframes"
version="2.1.22-26.2-port.1"
displayName="WaterFrames"
displayURL="https://www.curseforge.com/minecraft/mc-mods/waterframes"
credits="Models by FabiAcr and J-RAP. Textures by Kotyarendj"
authors="SrRapero720"
logoFile="pack.png"
description='''Display custom video and pictures in your world. NeoForge 26.2 compatibility port.'''

[[mixins]]
config="waterframes.mixin.json"

[[accessTransformers]]
file="META-INF/accesstransformer.cfg"

[[dependencies.waterframes]]
modId="neoforge"
type="required"
versionRange="[26.2.0.87,)"
ordering="NONE"
side="BOTH"

[[dependencies.waterframes]]
modId="minecraft"
type="required"
versionRange="[26.2,26.3)"
ordering="NONE"
side="BOTH"

[[dependencies.waterframes]]
modId="creativecore"
type="required"
versionRange="[2.14.16,)"
ordering="AFTER"
side="BOTH"

[[dependencies.waterframes]]
modId="watermedia"
type="required"
versionRange="[2.1.37,3)"
ordering="AFTER"
side="CLIENT"
""", encoding="utf-8")

# Resource-pack format changed in 26.2. The exact value is not load-critical for
# the Java port, but keeping metadata current avoids resource-pack warnings.
pack = DST / "src/main/resources/pack.mcmeta"
pack.write_text("""{
  "pack": {
    "description": "WaterFrames resources",
    "min_format": 81,
    "max_format": 81
  }
}
""", encoding="utf-8")

print("Prepared", DST)


# ---------------------------------------------------------------------------
# Mechanical 1.21.5 -> 26.2 Mojang/NeoForge renames
# ---------------------------------------------------------------------------
import re

java_root = DST / "src/main/java"
for java in java_root.rglob("*.java"):
    text = java.read_text(encoding="utf-8")

    text = text.replace("import net.minecraft.resources.ResourceLocation;", "import net.minecraft.resources.Identifier;")
    text = re.sub(r"\bResourceLocation\b", "Identifier", text)
    text = text.replace("import net.minecraft.Util;", "import net.minecraft.util.Util;")
    text = text.replace("import net.minecraft.client.gui.GuiGraphics;", "import net.minecraft.client.gui.GuiGraphicsExtractor;")
    text = re.sub(r"\bGuiGraphics\b", "GuiGraphicsExtractor", text)
    text = text.replace("import net.minecraft.client.renderer.RenderType;", "import net.minecraft.client.renderer.rendertype.RenderType;")

    # Null-default annotations were removed from the 26.x Minecraft package.
    text = text.replace("import net.minecraft.FieldsAreNonnullByDefault;\n", "")
    text = text.replace("import net.minecraft.MethodsReturnNonnullByDefault;\n", "")
    text = text.replace("@FieldsAreNonnullByDefault\n", "")
    text = text.replace("@MethodsReturnNonnullByDefault\n", "")

    # Level#isClientSide is a method in 26.2.
    text = re.sub(r"\.isClientSide\b(?!\s*\()", ".isClientSide()", text)

    # Identifier constructors are factories in 26.2.
    text = re.sub(
        r"new Identifier\(\s*([^,\n]+?)\s*,\s*([^)]+?)\s*\)",
        r"Identifier.fromNamespaceAndPath(\1, \2)",
        text
    )

    java.write_text(text, encoding="utf-8")

# WATERViSION is optional; keep WaterFrames functional without its external viewer.
renderer_wrapper = DST / "src/main/java/me/srrapero720/waterframes/client/rendering/RendererWrapper.java"
renderer_wrapper.write_text("""package me.srrapero720.waterframes.client.rendering;

import com.mojang.blaze3d.GpuFormat;
import com.mojang.blaze3d.opengl.FrameBufferCache;
import com.mojang.blaze3d.opengl.GlTexture;
import com.mojang.blaze3d.systems.RenderSystem;
import com.mojang.blaze3d.textures.FilterMode;
import com.mojang.blaze3d.textures.GpuTexture;
import net.minecraft.client.renderer.texture.AbstractTexture;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.api.distmarker.OnlyIn;
import org.watermedia.api.image.ImageRenderer;

@OnlyIn(Dist.CLIENT)
public class RendererWrapper extends AbstractTexture {
    private static final FrameBufferCache FRAME_BUFFER_CACHE = new FrameBufferCache();
    private final ImageRenderer renderer;
    private final ForeignGlTexture[] glTextures;

    public RendererWrapper(final ImageRenderer renderer) {
        this.renderer = renderer;
        this.glTextures = new ForeignGlTexture[renderer.textures.length];
        for (int i = 0; i < glTextures.length; i++) {
            glTextures[i] = new ForeignGlTexture(renderer.texture(i), renderer.width, renderer.height);
        }
        select(renderer.texture(0));
    }

    private void select(int id) {
        for (ForeignGlTexture candidate : glTextures) {
            if (candidate.glId() == id) {
                if (this.textureView != null) {
                    try { this.textureView.close(); } catch (Throwable ignored) {}
                }
                this.texture = candidate;
                this.textureView = RenderSystem.getDevice().createTextureView(candidate);
                this.sampler = RenderSystem.getSamplerCache().getClampToEdge(FilterMode.NEAREST);
                return;
            }
        }
    }

    public void update(int id) {
        select(id);
    }

    @Override
    public void close() {
        if (textureView != null) {
            try { textureView.close(); } catch (Throwable ignored) {}
            textureView = null;
        }
        texture = null;
        sampler = null;
    }

    private static final class ForeignGlTexture extends GlTexture {
        private boolean disposed;

        private ForeignGlTexture(int glId, int width, int height) {
            super(GpuTexture.USAGE_TEXTURE_BINDING, "waterframes-image", GpuFormat.RGBA8_UNORM,
                    width, height, 1, 1, glId, FRAME_BUFFER_CACHE);
        }

        @Override public void close() { disposed = true; }
        @Override public boolean isClosed() { return disposed; }
    }
}
""", encoding="utf-8")

texture_wrapper = DST / "src/main/java/me/srrapero720/waterframes/client/rendering/TextureWrapper.java"
texture_wrapper.write_text("""package me.srrapero720.waterframes.client.rendering;

import com.mojang.blaze3d.GpuFormat;
import com.mojang.blaze3d.opengl.FrameBufferCache;
import com.mojang.blaze3d.opengl.GlTexture;
import com.mojang.blaze3d.systems.RenderSystem;
import com.mojang.blaze3d.textures.FilterMode;
import com.mojang.blaze3d.textures.GpuTexture;
import net.minecraft.client.renderer.texture.AbstractTexture;

public class TextureWrapper extends AbstractTexture {
    private static final FrameBufferCache FRAME_BUFFER_CACHE = new FrameBufferCache();

    public TextureWrapper(final int id, final int width, final int height) {
        ForeignGlTexture foreign = new ForeignGlTexture(id, width, height);
        this.texture = foreign;
        this.textureView = RenderSystem.getDevice().createTextureView(foreign);
        this.sampler = RenderSystem.getSamplerCache().getClampToEdge(FilterMode.LINEAR);
    }

    @Override
    public void close() {
        if (textureView != null) {
            try { textureView.close(); } catch (Throwable ignored) {}
        }
        textureView = null;
        texture = null;
        sampler = null;
    }

    private static final class ForeignGlTexture extends GlTexture {
        private boolean disposed;
        private ForeignGlTexture(int glId, int width, int height) {
            super(GpuTexture.USAGE_TEXTURE_BINDING, "waterframes-video", GpuFormat.RGBA8_UNORM,
                    Math.max(1, width), Math.max(1, height), 1, 1, glId, FRAME_BUFFER_CACHE);
        }
        @Override public void close() { disposed = true; }
        @Override public boolean isClosed() { return disposed; }
    }
}
""", encoding="utf-8")

# The old CreativeCore UV mixin targeted a renderer implementation that no longer exists.
# 26.2 CreativeCore already emits color on its GUI textured vertices, so remove the mixin.
mixin_json = DST / "src/main/resources/waterframes.mixin.json"
mixin_json.write_text("""{
  "required": true,
  "compatibilityLevel": "JAVA_25",
  "package": "me.srrapero720.waterframes.mixin.impl",
  "minVersion": "0.8.7",
  "mixins": [
    "MinecraftServerMixin"
  ]
}
""", encoding="utf-8")
gui_mixin = DST / "src/main/java/me/srrapero720/waterframes/mixin/impl/creativecore/GuiRenderHelperMixin.java"
if gui_mixin.exists():
    gui_mixin.unlink()
