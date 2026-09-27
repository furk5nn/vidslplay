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


# ---------------------------------------------------------------------------
# Semantic 26.2 migration: loader, persistence, block API, renderer, GUI parents
# ---------------------------------------------------------------------------

def edit(rel, fn):
    p = DST / rel
    s = p.read_text(encoding="utf-8")
    p.write_text(fn(s), encoding="utf-8")

# NeoForge loader methods became instance methods.
for rel in [
    "src/main/java/me/srrapero720/waterframes/WaterFrames.java",
    "src/main/java/me/srrapero720/waterframes/DisplaysConfig.java",
]:
    edit(rel, lambda s: s
        .replace("FMLLoader.getDist()", "FMLLoader.getCurrent().getDist()")
        .replace("FMLLoader.getLoadingModList()", "FMLLoader.getCurrent().getLoadingModList()")
        .replace("FMLLoader.isProduction()", "FMLLoader.getCurrent().isProduction()")
    )

# ResourceKey and profile API changes.
edit("src/main/java/me/srrapero720/waterframes/common/block/DisplayBlock.java", lambda s: s
    .replace(".dimension().location()", ".dimension().identifier()")
    .replace("ChatFormatting.AQUA.getColor()", "0x55FFFF")
    .replace(
        "public int getAnalogOutputSignal(BlockState state, Level level, BlockPos pos) {",
        "public int getAnalogOutputSignal(BlockState state, Level level, BlockPos pos, Direction side) {"
    )
)

def config_262(s):
    s = s.replace("Level level = player.level;", "Level level = player.level();")
    s = s.replace("player.getGameProfile().getName()", "player.getGameProfile().name()")
    s = s.replace("integrated.isSingleplayerOwner(player.getGameProfile())", "integrated.isSingleplayerOwner(player.nameAndId())")
    return s
edit("src/main/java/me/srrapero720/waterframes/DisplaysConfig.java", config_262)

# DeferredRegister block item helpers now take a property supplier.
def registry_262(s):
    s = re.sub(
        r'registerSimpleBlockItem\("([^"]+)",\s*([A-Z_]+),\s*prop\(\)\)',
        r'registerSimpleBlockItem("\1", \2, () -> prop())',
        s
    )
    s = s.replace(
        "BlockEntityRenderers.register(TILE_FRAME.get(), DisplayRenderer::new);",
        "e.registerBlockEntityRenderer(TILE_FRAME.get(), DisplayRenderer::new);"
    ).replace(
        "BlockEntityRenderers.register(TILE_PROJECTOR.get(), DisplayRenderer::new);",
        "e.registerBlockEntityRenderer(TILE_PROJECTOR.get(), DisplayRenderer::new);"
    ).replace(
        "BlockEntityRenderers.register(TILE_TV.get(), DisplayRenderer::new);",
        "e.registerBlockEntityRenderer(TILE_TV.get(), DisplayRenderer::new);"
    ).replace(
        "BlockEntityRenderers.register(TILE_BIG_TV.get(), DisplayRenderer::new);",
        "e.registerBlockEntityRenderer(TILE_BIG_TV.get(), DisplayRenderer::new);"
    ).replace(
        "BlockEntityRenderers.register(TILE_TV_BOX.get(), DisplayRenderer::new);",
        "e.registerBlockEntityRenderer(TILE_TV_BOX.get(), DisplayRenderer::new);"
    )
    return s
edit("src/main/java/me/srrapero720/waterframes/DisplaysRegistry.java", registry_262)

# 26.2 persistence is ValueInput/ValueOutput. Keep CompoundTag for GUI/network payloads.
def data_262(s):
    if "net.minecraft.world.level.storage.ValueInput" not in s:
        s = s.replace(
            "import net.minecraft.nbt.CompoundTag;",
            "import net.minecraft.nbt.CompoundTag;\nimport net.minecraft.world.level.storage.ValueInput;\nimport net.minecraft.world.level.storage.ValueOutput;"
        )
    s = s.replace("public void save(CompoundTag nbt, DisplayTile tile)", "public void save(ValueOutput nbt, DisplayTile tile)")
    s = s.replace("public void load(CompoundTag nbt, DisplayTile tile)", "public void load(ValueInput nbt, DisplayTile tile)")
    s = s.replace("this.tick = nbt.getIntOr(TICK, 0);", "this.tick = nbt.getLongOr(TICK, 0L);")
    s = s.replace("this.tickMax = nbt.getIntOr(TICK_MAX, this.tickMax);", "this.tickMax = nbt.getLongOr(TICK_MAX, this.tickMax);")
    s = s.replace("screen.flip_x.value", "screen.flip_x.getValue()")
    s = s.replace("screen.flip_y.value", "screen.flip_y.getValue()")
    s = s.replace("screen.show_model.value", "screen.show_model.getValue()")
    s = s.replace("screen.lit.value", "screen.lit.getValue()")
    s = s.replace("screen.mirror.value", "screen.mirror.getState()")
    return s
edit("src/main/java/me/srrapero720/waterframes/common/block/data/DisplayData.java", data_262)

def tile_262(s):
    s = s.replace(
        "import net.minecraft.nbt.CompoundTag;",
        "import net.minecraft.nbt.CompoundTag;\nimport net.minecraft.world.level.storage.ValueInput;\nimport net.minecraft.world.level.storage.ValueOutput;"
    )
    s = re.sub(
        r'@Override\s+protected void saveAdditional\(CompoundTag nbt, HolderLookup\.Provider registries\) \{\s*this\.data\.save\(nbt, this\);\s*super\.saveAdditional\(nbt, registries\);\s*\}',
        '''@Override
    protected void saveAdditional(ValueOutput output) {
        this.data.save(output, this);
        super.saveAdditional(output);
    }''',
        s, flags=re.S
    )
    s = re.sub(
        r'@Override\s+protected void loadAdditional\(CompoundTag nbt, HolderLookup\.Provider registries\) \{\s*this\.data\.load\(nbt, this\);\s*super\.loadAdditional\(nbt, registries\);\s*\}',
        '''@Override
    protected void loadAdditional(ValueInput input) {
        this.data.load(input, this);
        super.loadAdditional(input);
    }''',
        s, flags=re.S
    )
    s = re.sub(
        r'@Override\s+public void handleUpdateTag\(CompoundTag tag, HolderLookup\.Provider lookupProvider\) \{\s*super\.handleUpdateTag\(tag, lookupProvider\);\s*this\.data\.load\(tag, this\);\s*this\.setDirty\(\);\s*\}',
        '''@Override
    public void handleUpdateTag(ValueInput input) {
        super.handleUpdateTag(input);
        this.data.load(input, this);
        this.setDirty();
    }''',
        s, flags=re.S
    )
    return s
edit("src/main/java/me/srrapero720/waterframes/common/block/entity/DisplayTile.java", tile_262)

# Full 26.2 block-entity renderer port. State extraction owns all world/tile reads;
# submission only consumes immutable-ish frame data.
renderer = DST / "src/main/java/me/srrapero720/waterframes/client/rendering/DisplayRenderer.java"
renderer.write_text("""package me.srrapero720.waterframes.client.rendering;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import me.srrapero720.waterframes.DisplaysConfig;
import me.srrapero720.waterframes.WaterFrames;
import me.srrapero720.waterframes.common.block.entity.DisplayTile;
import net.minecraft.client.renderer.LightTexture;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderer;
import net.minecraft.client.renderer.blockentity.BlockEntityRendererProvider;
import net.minecraft.client.renderer.blockentity.state.BlockEntityRenderState;
import net.minecraft.client.renderer.feature.ModelFeatureRenderer;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.state.level.CameraRenderState;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Vec3i;
import net.minecraft.resources.Identifier;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;
import team.creative.creativecore.common.util.math.base.Axis;
import team.creative.creativecore.common.util.math.base.Facing;
import team.creative.creativecore.common.util.math.box.AlignedBox;
import team.creative.creativecore.common.util.math.box.BoxCorner;
import team.creative.creativecore.common.util.math.box.BoxFace;

public final class DisplayRenderer implements BlockEntityRenderer<DisplayTile, DisplayRenderer.State> {

    public DisplayRenderer(BlockEntityRendererProvider.Context context) {}

    public static final class State extends BlockEntityRenderState {
        boolean valid;
        AlignedBox box;
        Facing facing;
        BoxFace boxFace;
        boolean front;
        boolean back;
        boolean flipX;
        boolean flipY;
        boolean projects;
        int color;
        float rotation;
        boolean loading;
        boolean buffering;
        Identifier texture;
    }

    @Override
    public State createRenderState() {
        return new State();
    }

    @Override
    public void extractRenderState(
            DisplayTile tile,
            State state,
            float partialTicks,
            Vec3 cameraPosition,
            ModelFeatureRenderer.@Nullable CrumblingOverlay breakProgress) {
        BlockEntityRenderer.super.extractRenderState(tile, state, partialTicks, cameraPosition, breakProgress);
        state.valid = false;
        state.texture = null;
        state.loading = false;
        state.buffering = false;

        if (!DisplaysConfig.keepsRendering()) return;
        var display = tile.activeDisplay();
        if (display == null) return;

        display.preRender();

        var direction = tile.getDirection();
        var box = new AlignedBox(tile.getRenderBox());
        boolean invertedFace = tile.caps.invertedFace(tile);
        var boxFace = BoxFace.get(Facing.get(invertedFace ? direction.getOpposite() : direction));
        var facing = boxFace.facing;

        if (tile.caps.growMax(tile, facing, invertedFace)) {
            box.setMax(facing.axis, box.getMax(facing.axis) + tile.caps.growSize());
        } else {
            box.setMin(facing.axis, box.getMin(facing.axis) - tile.caps.growSize());
        }

        state.box = box;
        state.boxFace = boxFace;
        state.facing = facing;
        state.projects = tile.caps.projects();
        state.front = !state.projects || tile.data.renderBothSides;
        state.back = state.projects || tile.data.renderBothSides;
        state.flipX = state.projects != tile.data.flipX;
        state.flipY = tile.data.flipY;
        state.rotation = tile.data.rotation;
        int c = tile.data.brightness & 0xFF;
        int a = tile.data.alpha & 0xFF;
        state.color = (a << 24) | (c << 16) | (c << 8) | c;
        state.loading = display.isLoading();
        state.buffering = display.isBuffering();
        if (display.canRender()) state.texture = display.getTextureId();
        state.valid = state.loading || state.buffering || state.texture != null;
    }

    @Override
    public void submit(State state, PoseStack poseStack, SubmitNodeCollector collector, CameraRenderState camera) {
        if (!state.valid || state.box == null || state.boxFace == null || state.facing == null) return;

        poseStack.pushPose();
        poseStack.translate(0.5, 0.5, 0.5);
        poseStack.mulPose(state.facing.rotation().rotation((float) Math.toRadians(-state.rotation)));
        poseStack.translate(-0.5, -0.5, -0.5);

        if (state.loading) {
            submitFace(state, loadingBox(state.box, state.facing, state.projects),
                    WaterFrames.LOADING_ANIMATION, poseStack, collector);
        } else if (state.texture != null) {
            submitFace(state, state.box, state.texture, poseStack, collector);
            if (state.buffering) {
                submitFace(state, loadingBox(state.box, state.facing, state.projects),
                        WaterFrames.LOADING_ANIMATION, poseStack, collector);
            }
        }
        poseStack.popPose();
    }

    private static void submitFace(State state, AlignedBox box, Identifier texture,
                                   PoseStack poseStack, SubmitNodeCollector collector) {
        collector.submitCustomGeometry(
                poseStack,
                RenderTypes.entityTranslucent(texture),
                (pose, builder) -> emitFace(state, box, pose, builder)
        );
    }

    private static void emitFace(State state, AlignedBox box, PoseStack.Pose pose, VertexConsumer builder) {
        if (state.front) {
            for (int i = 0; i < state.boxFace.corners.length; i++) {
                emitVertex(state, box, state.boxFace.corners[i], pose, builder);
            }
        }
        if (state.back) {
            for (int i = state.boxFace.corners.length - 1; i >= 0; i--) {
                emitVertex(state, box, state.boxFace.corners[i], pose, builder);
            }
        }
    }

    private static void emitVertex(State state, AlignedBox box, BoxCorner corner,
                                   PoseStack.Pose pose, VertexConsumer builder) {
        Vec3i normal = state.facing.normal;
        int color = state.color;
        int r = (color >>> 16) & 0xFF;
        int g = (color >>> 8) & 0xFF;
        int b = color & 0xFF;
        int a = (color >>> 24) & 0xFF;
        builder.addVertex(pose, box.get(corner.x), box.get(corner.y), box.get(corner.z))
                .setColor(r, g, b, a)
                .setUv(corner.isFacing(state.boxFace.getTexU()) != state.flipX ? 1f : 0f,
                       corner.isFacing(state.boxFace.getTexV()) != state.flipY ? 1f : 0f)
                .setOverlay(OverlayTexture.NO_OVERLAY)
                .setLight(LightTexture.FULL_BRIGHT)
                .setNormal(pose, normal.getX(), normal.getY(), normal.getZ());
    }

    private static AlignedBox loadingBox(AlignedBox parent, Facing facing, boolean projects) {
        AlignedBox box = new AlignedBox(parent);
        Axis one = facing.one();
        Axis two = facing.two();
        float width = box.getSize(one);
        float height = box.getSize(two);

        if (width > height) {
            float subtracts = (width - height) / 2f;
            float margin = height / 4f;
            box.setMin(one, box.getMin(one) + subtracts + margin);
            box.setMax(one, box.getMax(one) - subtracts - margin);
            box.setMin(two, box.getMin(two) + margin);
            box.setMax(two, box.getMax(two) - margin);
        } else if (height > width) {
            float subtracts = (height - width) / 2f;
            float margin = width / 4f;
            box.setMin(two, box.getMin(two) + subtracts + margin);
            box.setMax(two, box.getMax(two) - subtracts - margin);
            box.setMin(one, box.getMin(one) + margin);
            box.setMax(one, box.getMax(one) - margin);
        }

        if (facing.positive) {
            box.setMax(facing.axis, parent.getMax(facing.axis) + (projects ? -0.001f : 0.001f));
        } else {
            box.setMin(facing.axis, parent.getMin(facing.axis) - (projects ? -0.001f : 0.001f));
        }
        return box;
    }

    @Override
    public boolean shouldRenderOffScreen() {
        return true;
    }

    @Override
    public int getViewDistance() {
        return Math.max(128, DisplaysConfig.maxRenDis());
    }

    @Override
    public boolean shouldRender(DisplayTile tile, Vec3 cameraPos) {
        BlockPos tilePos = tile.getBlockPos().relative(tile.getDirection(), (int) tile.data.projectionDistance);
        return Vec3.atCenterOf(tilePos).closerThan(cameraPos, tile.data.renderDistance);
    }
}
""", encoding="utf-8")

# CreativeCore 26.x controls require an IGuiParent at construction.
# Screens can safely create direct children against themselves; add() re-parents nested children.
screen_files = [
    "src/main/java/me/srrapero720/waterframes/common/screens/DisplayScreen.java",
    "src/main/java/me/srrapero720/waterframes/common/screens/PlayListScreen.java",
    "src/main/java/me/srrapero720/waterframes/common/screens/RemoteControlScreen.java",
]
constructors = [
    "GuiLabel", "GuiIcon", "GuiButtonIcon", "GuiCheckBox", "GuiCheckButtonIcon",
    "GuiStateButtonIcon", "GuiCounterDecimal", "GuiSlider", "GuiSteppedSlider",
    "GuiSeekBar", "GuiButton", "GuiScrollY"
]
for rel in screen_files:
    p = DST / rel
    s = p.read_text(encoding="utf-8")
    # Layer constructor now carries the side explicitly.
    if "DisplayScreen.java" in rel:
        s = s.replace('super("display_screen", WIDTH, HEIGHT);', 'super(tile.isClient(), "display_screen", WIDTH, HEIGHT);')
    elif "PlayListScreen.java" in rel:
        s = s.replace('super("display_screen", WIDTH, HEIGHT);', 'super(tile.isClient(), "display_screen", WIDTH, HEIGHT);')
    else:
        s = s.replace('super("remote_screen", WIDTH, HEIGHT);', 'super(tile.isClient(), "remote_screen", WIDTH, HEIGHT);')

    for klass in constructors:
        s = re.sub(rf'new {klass}\((?!this,)', f'new {klass}(this, ', s)

    # GuiParent constructor family.
    s = re.sub(r'new GuiParent\(\)', 'new GuiParent(this)', s)
    s = re.sub(r'new GuiParent\((GuiFlow\.)', r'new GuiParent(this, \1', s)
    s = re.sub(r'new GuiParent\("', 'new GuiParent(this, "', s)

    # Current check widgets expose getters/setters instead of public state fields.
    s = s.replace(".playback.value", ".playback.getState()")
    s = s.replace(".loop.value", ".loop.getState()")
    s = s.replace(".mirror.value", ".mirror.getState()")
    s = s.replace("playButton.value", "playButton.getState()")
    s = s.replace("show_model.set(", "show_model.setValue(")
    s = s.replace("lit.set(", "lit.setValue(")
    s = s.replace("shaderMode.set(", "shaderMode.setValue(")

    p.write_text(s, encoding="utf-8")

# Parent-aware custom controls / tables.
pair = DST / "src/main/java/me/srrapero720/waterframes/common/screens/widgets/WidgetPairTable.java"
s = pair.read_text(encoding="utf-8")
s = s.replace("import team.creative.creativecore.common.gui.GuiControl;", "import team.creative.creativecore.common.gui.GuiControl;\nimport team.creative.creativecore.common.gui.IGuiParent;")
s = s.replace("public WidgetPairTable(GuiFlow columGuiFlow) {", "public WidgetPairTable(IGuiParent parent, GuiFlow columGuiFlow) {")
s = s.replace("this(columGuiFlow, 0);", "this(parent, columGuiFlow, 0);")
s = s.replace("public WidgetPairTable(GuiFlow columGuiFlow, int spacing) {", "public WidgetPairTable(IGuiParent parent, GuiFlow columGuiFlow, int spacing) {")
s = s.replace("this(columGuiFlow, Align.LEFT, spacing);", "this(parent, columGuiFlow, Align.LEFT, spacing);")
s = s.replace("public WidgetPairTable(GuiFlow defaultFlow, Align align, int spacing) {", "public WidgetPairTable(IGuiParent parent, GuiFlow defaultFlow, Align align, int spacing) {\n        super(parent);")
s = s.replace("this.spacing = spacing;", "this.setSpacing(spacing);")
s = s.replace("this.align = align;", "this.setAlign(align);")
s = s.replace("this.left.align = Align.LEFT;", "this.left.setAlign(Align.LEFT);")
s = s.replace("this.right.align = Align.RIGHT;", "this.right.setAlign(Align.RIGHT);")
s = s.replace("left.flow = flow;", "left.setFlow(flow);")
s = s.replace("right.flow = flow;", "right.setFlow(flow);")
s = s.replace("return new GuiRow(left = new GuiColumn(), right = new GuiColumn());",
              "return new GuiRow(this, left = new GuiColumn(this), right = new GuiColumn(this));")
s = s.replace("this.left.flow = flow;", "this.left.setFlow(flow);")
s = s.replace("this.right.flow = flow;", "this.right.setFlow(flow);")
s = s.replace("this.flow = flow;", "super.setFlow(flow);")
pair.write_text(s, encoding="utf-8")

triple = DST / "src/main/java/me/srrapero720/waterframes/common/screens/widgets/WidgetTripleTable.java"
s = triple.read_text(encoding="utf-8")
s = s.replace("import team.creative.creativecore.common.gui.GuiControl;", "import team.creative.creativecore.common.gui.GuiControl;\nimport team.creative.creativecore.common.gui.IGuiParent;")
s = s.replace("public WidgetTripleTable(GuiFlow columGuiFlow) {\n        super(columGuiFlow);",
              "public WidgetTripleTable(IGuiParent parent, GuiFlow columGuiFlow) {\n        super(parent, columGuiFlow);")
s = s.replace("this.center.align = Align.CENTER;", "this.center.setAlign(Align.CENTER);")
s = s.replace("return new GuiRow(left = new GuiColumn(), center = new GuiColumn(), right = new GuiColumn());",
              "return new GuiRow(this, left = new GuiColumn(this), center = new GuiColumn(this), right = new GuiColumn(this));")
s = s.replace("center.flow = flow;", "center.setFlow(flow);")
triple.write_text(s, encoding="utf-8")

# Basic custom control constructors.
custom_specs = {
    "WidgetURLTextField.java": (
        "import team.creative.creativecore.common.gui.GuiControl;",
        "import team.creative.creativecore.common.gui.GuiControl;\nimport team.creative.creativecore.common.gui.IGuiParent;",
        "public WidgetURLTextField(DisplayTile tile) {",
        "public WidgetURLTextField(IGuiParent parent, DisplayTile tile) {",
        "super(DisplayData.URL);",
        "super(parent, DisplayData.URL);"
    ),
    "WidgetStatusIcon.java": (
        "import team.creative.creativecore.common.gui.control.simple.GuiIcon;",
        "import team.creative.creativecore.common.gui.IGuiParent;\nimport team.creative.creativecore.common.gui.control.simple.GuiIcon;",
        "public WidgetStatusIcon(String name, Icon icon, DisplayTile tile) {",
        "public WidgetStatusIcon(IGuiParent parent, String name, Icon icon, DisplayTile tile) {",
        "super(name, icon);",
        "super(parent, name, icon);"
    ),
    "WidgetClickableArea.java": (
        "import team.creative.creativecore.common.gui.control.simple.GuiIcon;",
        "import team.creative.creativecore.common.gui.IGuiParent;\nimport team.creative.creativecore.common.gui.control.simple.GuiIcon;",
        "public WidgetClickableArea(String name, PositionHorizontal x, PositionVertical y) {",
        "public WidgetClickableArea(IGuiParent parent, String name, PositionHorizontal x, PositionVertical y) {",
        "super(name, IconStyles.POS_BASE);",
        "super(parent, name, IconStyles.POS_BASE);"
    ),
    "WidgetPlaylistEntry.java": (
        "import team.creative.creativecore.common.gui.GuiParent;",
        "import team.creative.creativecore.common.gui.GuiParent;\nimport team.creative.creativecore.common.gui.IGuiParent;",
        "public WidgetPlaylistEntry(DisplayTile tile, LinkedList<URI> list, URI uri) {",
        "public WidgetPlaylistEntry(IGuiParent parent, DisplayTile tile, LinkedList<URI> list, URI uri) {",
        'super("experimental_element_" + uri.toString());',
        'super(parent, "experimental_element_" + uri.toString());'
    ),
}
for file, spec in custom_specs.items():
    p = DST / "src/main/java/me/srrapero720/waterframes/common/screens/widgets" / file
    s = p.read_text(encoding="utf-8")
    s = s.replace(spec[0], spec[1]).replace(spec[2], spec[3]).replace(spec[4], spec[5])
    # Nested direct children use this custom parent.
    for klass in ["GuiLabel", "GuiButtonIcon"]:
        s = re.sub(rf'new {klass}\((?!this,)', f'new {klass}(this, ', s)
    s = re.sub(r'new GuiParent\(\)', 'new GuiParent(this)', s)
    s = re.sub(r'new GuiParent\("', 'new GuiParent(this, "', s)
    p.write_text(s, encoding="utf-8")

# Update custom-widget call sites now that their constructors are parent-aware.
for rel in screen_files:
    p = DST / rel
    s = p.read_text(encoding="utf-8")
    s = re.sub(r'new WidgetPairTable\((?!this,)', 'new WidgetPairTable(this, ', s)
    s = re.sub(r'new WidgetTripleTable\((?!this,)', 'new WidgetTripleTable(this, ', s)
    s = re.sub(r'new WidgetClickableArea\((?!this,)', 'new WidgetClickableArea(this, ', s)
    s = re.sub(r'new WidgetStatusIcon\((?!this,)', 'new WidgetStatusIcon(this, ', s)
    s = s.replace("new WidgetURLTextField(this.tile)", "new WidgetURLTextField(this, this.tile)")
    s = s.replace("new WidgetURLTextField(null)", "new WidgetURLTextField(this, null)")
    # Entries added to the list should originate under the list parent.
    s = s.replace("new WidgetPlaylistEntry(tile, this.uris,", "new WidgetPlaylistEntry(this.list, tile, this.uris,")
    p.write_text(s, encoding="utf-8")

# Remote screen also uses pair/triple custom tables after the generic pass.
