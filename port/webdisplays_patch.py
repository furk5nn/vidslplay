from pathlib import Path
import shutil, re

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "reference" / "webdisplays-brotherbill-1.21.1"
DST = ROOT / "build-port" / "webdisplays"

if DST.exists():
    shutil.rmtree(DST)
shutil.copytree(SRC, DST)

(DST / "settings.gradle").write_text('rootProject.name = "webdisplays-26.2-port"\n', encoding="utf-8")
(DST / "gradle.properties").write_text("""org.gradle.jvmargs=-Xmx4G
org.gradle.daemon=false
systemProp.file.encoding=utf-8
""", encoding="utf-8")

(DST / "build.gradle").write_text("""plugins {
    id 'java'
    id 'net.neoforged.moddev' version '2.0.147'
}

version = '2.0.2-26.2-port.1'
group = 'net.montoyo.wd'

base { archivesName = 'webdisplays-NEOFORGE-mc26.2' }

java.toolchain.languageVersion = JavaLanguageVersion.of(25)

repositories {
    mavenCentral()
    maven {
        name = 'Keksuccino Maven'
        url = 'https://keksuccino.github.io/maven/'
    }
    maven {
        url = 'https://www.cursemaven.com'
        content { includeGroup 'curse.maven' }
    }
}

dependencies {
    implementation 'de.keksuccino:mcef-neoforge:2.2.0-26.1.1'
    implementation fileTree(dir: '../waterframes/build/libs', include: ['*.jar'])
}

neoForge {
    version = '26.2.0.87'
    runs {
        client { client() }
        server { server() }
    }
    mods {
        webdisplays { sourceSet sourceSets.main }
    }
}

tasks.withType(JavaCompile).configureEach {
    options.encoding = 'UTF-8'
}
""", encoding="utf-8")

meta = DST / "src/main/resources/META-INF/neoforge.mods.toml"
meta.write_text("""modLoader="javafml"
loaderVersion="[4,)"
license="MIT"

[[mods]]
modId="webdisplays"
version="2.0.2-26.2-port.1"
displayName="WebDisplays"
displayURL="https://github.com/CinemaMod/webdisplays"
authors="GiantLuigi4, ds58, Mysticpasta1, montoyo, WaterPicker"
description='''WebDisplays port for NeoForge 26.2 with client-local file playback through WaterFrames.'''

[[dependencies.webdisplays]]
modId="neoforge"
type="required"
versionRange="[26.2.0.87,)"
ordering="NONE"
side="BOTH"

[[dependencies.webdisplays]]
modId="minecraft"
type="required"
versionRange="[26.2,26.3)"
ordering="NONE"
side="BOTH"

[[dependencies.webdisplays]]
modId="mcef"
type="required"
versionRange="[2.2.0,)"
ordering="AFTER"
side="CLIENT"

[[dependencies.webdisplays]]
modId="waterframes"
type="required"
versionRange="[2.1.22-26.2-port.1,)"
ordering="AFTER"
side="CLIENT"

[[mixins]]
config="webdisplays.mixins.json"
""", encoding="utf-8")

# Mechanical Mojang 26.x renames. Semantic renderer/model/NBT migrations follow
# from compiler feedback rather than broad guessing.
for java in (DST / "src/main/java").rglob("*.java"):
    s = java.read_text(encoding="utf-8")
    s = s.replace("import net.minecraft.resources.ResourceLocation;", "import net.minecraft.resources.Identifier;")
    s = re.sub(r"\bResourceLocation\b", "Identifier", s)
    s = s.replace("import net.minecraft.Util;", "import net.minecraft.util.Util;")
    s = s.replace("import net.minecraft.client.gui.GuiGraphics;", "import net.minecraft.client.gui.GuiGraphicsExtractor;")
    s = re.sub(r"\bGuiGraphics\b", "GuiGraphicsExtractor", s)
    s = s.replace("import net.minecraft.client.renderer.RenderType;", "import net.minecraft.client.renderer.rendertype.RenderType;")
    s = s.replace("import net.minecraft.client.renderer.RenderStateShard;", "import net.minecraft.client.renderer.rendertype.RenderStateShard;")
    s = re.sub(r"\.isClientSide\b(?!\s*\()", ".isClientSide()", s)
    s = s.replace(".isClientSide()()", ".isClientSide()")
    s = s.replace("Identifier.fromNamespaceAndPath", "Identifier.fromNamespaceAndPath")
    s = re.sub(
        r"new Identifier\(\s*([^,\n]+?)\s*,\s*([^)]+?)\s*\)",
        r"Identifier.fromNamespaceAndPath(\1, \2)",
        s
    )
    java.write_text(s, encoding="utf-8")


# 26.2 mechanical API migrations shared across the old WebDisplays source.
for java in (DST / "src/main/java").rglob("*.java"):
    s = java.read_text(encoding="utf-8")

    # Entity/package moves.
    s = s.replace("net.minecraft.world.entity.animal.Ocelot", "net.minecraft.world.entity.animal.feline.Ocelot")

    # Mojang still spells this historical package 'critereon' in the 26.2 mappings.
    s = s.replace("net.minecraft.advancements.criterion.", "net.minecraft.advancements.critereon.")

    # Block interaction API uses InteractionResult in 26.2.
    s = s.replace("import net.minecraft.world.ItemInteractionResult;\n", "")
    s = s.replace("import net.minecraft.world.InteractionResultHolder;\n", "")
    s = re.sub(r"\bItemInteractionResult\b", "InteractionResult", s)
    s = re.sub(r"\bInteractionResultHolder<\s*ItemStack\s*>\b", "InteractionResult", s)
    s = re.sub(r"InteractionResultHolder\.success\([^)]*\)", "InteractionResult.SUCCESS", s)
    s = re.sub(r"InteractionResultHolder\.pass\([^)]*\)", "InteractionResult.PASS", s)
    s = re.sub(r"InteractionResultHolder\.consume\([^)]*\)", "InteractionResult.CONSUME", s)

    # DirectionProperty was folded into EnumProperty<Direction>.
    s = s.replace(
        "import net.minecraft.world.level.block.state.properties.DirectionProperty;\n",
        "import net.minecraft.world.level.block.state.properties.EnumProperty;\n"
    )
    s = re.sub(r"\bDirectionProperty\b", "EnumProperty<Direction>", s)

    # Model/render package moves in 26.2.
    s = s.replace(
        "import net.minecraft.client.renderer.block.model.BakedQuad;",
        "import net.minecraft.client.resources.model.geometry.BakedQuad;"
    )
    s = s.replace(
        "import net.minecraft.client.resources.model.Material;",
        "import net.minecraft.client.resources.model.sprite.Material;"
    )
    s = s.replace(
        "import net.minecraft.client.resources.model.ModelState;",
        "import net.minecraft.client.renderer.block.dispatch.ModelState;"
    )
    s = s.replace(
        "import net.minecraft.world.level.BlockAndTintGetter;",
        "import net.minecraft.client.renderer.block.BlockAndTintGetter;"
    )
    s = s.replace(
        "import net.minecraft.client.renderer.block.model.ItemTransforms;",
        "import net.minecraft.client.resources.model.cuboid.ItemTransforms;"
    )

    if "InteractionResult " in s and "import net.minecraft.world.InteractionResult;" not in s:
        pkg_end = s.find("\n", s.find("package "))
        s = s[:pkg_end + 1] + "import net.minecraft.world.InteractionResult;\n" + s[pkg_end + 1:]

    java.write_text(s, encoding="utf-8")


# The old NeoForge dynamic ModelData path used by WebDisplays was removed in
# 26.2. Keep the original screen textures, but move adjacency/frame selection
# into the stateful panel renderer rather than reviving obsolete APIs.
for obsolete in [
    "src/main/java/net/montoyo/wd/client/renderers/ScreenBaker.java",
    "src/main/java/net/montoyo/wd/client/renderers/ScreenThinBaker.java",
    "src/main/java/net/montoyo/wd/client/renderers/ScreenModelLoader.java",
    "src/main/java/net/montoyo/wd/client/renderers/ScreenThinModelLoader.java",
]:
    p = DST / obsolete
    if p.exists():
        p.unlink()

client_proxy = DST / "src/main/java/net/montoyo/wd/client/ClientProxy.java"
if client_proxy.exists():
    s = client_proxy.read_text(encoding="utf-8")
    old = """\tpublic static void onModelRegistryEvent(ModelEvent.RegisterGeometryLoaders event) {
\t\tevent.register(ScreenModelLoader.SCREEN_LOADER, new ScreenModelLoader());
\t\tevent.register(ScreenThinModelLoader.LOADER_ID, new ScreenThinModelLoader());
\t}
"""
    s = s.replace(old, "")
    s = s.replace("import net.neoforged.neoforge.client.event.ModelEvent;\n", "")
    s = s.replace("import net.montoyo.wd.client.renderers.ScreenModelLoader;\n", "")
    s = s.replace("import net.montoyo.wd.client.renderers.ScreenThinModelLoader;\n", "")
    client_proxy.write_text(s, encoding="utf-8")

webdisplays_java = DST / "src/main/java/net/montoyo/wd/WebDisplays.java"
if webdisplays_java.exists():
    s = webdisplays_java.read_text(encoding="utf-8")
    s = s.replace("            bus.addListener(ClientProxy::onModelRegistryEvent);\n", "")
    webdisplays_java.write_text(s, encoding="utf-8")

# Seam-free neutral body. The outer panel frame is rendered once from the
# ScreenData multiblock dimensions, so no per-block interior bezel remains.
model_dir = DST / "src/main/resources/assets/webdisplays/models/block"
(model_dir / "screen.json").write_text("""{
  "parent": "minecraft:block/cube_all",
  "textures": { "all": "webdisplays:block/screen0" }
}
""", encoding="utf-8")
(model_dir / "screen_thin.json").write_text("""{
  "parent": "minecraft:block/cube_all",
  "textures": { "all": "webdisplays:block/screen0" }
}
""", encoding="utf-8")


# Stage the non-screen item renderers behind no-op compatibility shells while the
# 26.2 screen pipeline is brought up. Their gameplay items remain registered.
render_dir = DST / "src/main/java/net/montoyo/wd/client/renderers"
(render_dir / "IItemRenderer.java").write_text("""package net.montoyo.wd.client.renderers;

public interface IItemRenderer {
}
""", encoding="utf-8")

(render_dir / "MinePadRenderer.java").write_text("""package net.montoyo.wd.client.renderers;

public final class MinePadRenderer implements IItemRenderer {
    public MinePadRenderer() {
    }

    public static boolean renderAtSide(float side) {
        return true;
    }
}
""", encoding="utf-8")

(render_dir / "LaserPointerRenderer.java").write_text("""package net.montoyo.wd.client.renderers;

public final class LaserPointerRenderer implements IItemRenderer {
    public LaserPointerRenderer() {
    }

    public static boolean isOn() {
        return false;
    }
}
""", encoding="utf-8")

(render_dir / "ModelMinePad.java").write_text("""package net.montoyo.wd.client.renderers;

public final class ModelMinePad {
}
""", encoding="utf-8")

# Remove old hand-render/highlight hooks that use APIs removed in 26.2. They are
# restored later with the new item feature-renderer API.
client_proxy = DST / "src/main/java/net/montoyo/wd/client/ClientProxy.java"
if client_proxy.exists():
    s = client_proxy.read_text(encoding="utf-8")
    s = s.replace("import com.mojang.blaze3d.platform.GlStateManager;", "import com.mojang.blaze3d.opengl.GlStateManager;")
    s = s.replace("import net.neoforged.neoforge.client.event.RenderHighlightEvent;\n", "")
    s = re.sub(r"\n\s*@SubscribeEvent\s+public void onRenderPlayerHand\(RenderHandEvent ev\) \{.*?\n\s*\}", "\n", s, flags=re.S)
    s = re.sub(r"\n\s*public static void onDrawSelection\(RenderHighlightEvent\.Block event\) \{.*?\n\s*\}", "\n", s, flags=re.S)
    client_proxy.write_text(s, encoding="utf-8")

webdisplays_java = DST / "src/main/java/net/montoyo/wd/WebDisplays.java"
if webdisplays_java.exists():
    s = webdisplays_java.read_text(encoding="utf-8")
    s = s.replace("            NeoForge.EVENT_BUS.addListener(ClientProxy::onDrawSelection);\n", "")
    # Advancement trigger registration changed heavily in 26.2 and is unrelated
    # to screen playback; remove it from the core-port stage.
    s = re.sub(r"\s*public static final DeferredRegister<CriterionTrigger<\?>> TRIGGERS =.*?CRITERION_KEYBOARD_CAT =\s*TRIGGERS\.register\([^;]+;\n", "\n", s, flags=re.S)
    s = s.replace("        TRIGGERS.register(bus);\n", "")
    s = s.replace("import net.minecraft.advancements.CriterionTrigger;\n", "")
    s = s.replace("import net.montoyo.wd.core.WDCriterion;\n", "")
    webdisplays_java.write_text(s, encoding="utf-8")

wdcriterion = DST / "src/main/java/net/montoyo/wd/core/WDCriterion.java"
if wdcriterion.exists():
    wdcriterion.unlink()

# Remove calls to the staged-out custom advancements.
for rel in [
    "src/main/java/net/montoyo/wd/entity/KeyboardBlockEntity.java",
    "src/main/java/net/montoyo/wd/item/ItemLinker.java",
    "src/main/java/net/montoyo/wd/item/ItemMinePad2.java",
    "src/main/java/net/montoyo/wd/block/ScreenBlock.java",
]:
    p = DST / rel
    if p.exists():
        s = p.read_text(encoding="utf-8")
        s = re.sub(r"\s*if\s*\([^\n]*instanceof ServerPlayer[^\n]*\)\s*\n\s*WebDisplays\.CRITERION_[A-Z_]+\.get\(\)\.trigger\([^;]+;\n", "\n", s)
        p.write_text(s, encoding="utf-8")

# CompoundTag getters return Optional values in 26.2. These classes still use
# CompoundTag as their own serialized payload format, so unwrap with safe defaults.
screen_data = DST / "src/main/java/net/montoyo/wd/entity/ScreenData.java"
if screen_data.exists():
    s = screen_data.read_text(encoding="utf-8")
    s = re.sub(r'tag\.getByte\("([^"]+)"\)', r'tag.getByte("\1").orElse((byte) 0)', s)
    s = re.sub(r'tag\.getInt\("([^"]+)"\)', r'tag.getInt("\1").orElse(0)', s)
    s = re.sub(r'tag\.getLong\("([^"]+)"\)', r'tag.getLong("\1").orElse(0L)', s)
    s = re.sub(r'tag\.getDouble\("([^"]+)"\)', r'tag.getDouble("\1").orElse(0.0)', s)
    s = re.sub(r'tag\.getBoolean\("([^"]+)"\)', r'tag.getBoolean("\1").orElse(false)', s)
    s = re.sub(r'tag\.getString\("([^"]+)"\)', r'tag.getString("\1").orElse("")', s)
    s = re.sub(r'tag\.getUUID\("([^"]+)"\)', r'tag.getUUID("\1").orElse(new java.util.UUID(0L, 0L))', s)
    s = re.sub(r'tag\.getList\("([^"]+)",\s*[^)]+\)', r'tag.getList("\1").orElseGet(ListTag::new)', s)
    s = re.sub(r'friends\.getCompound\(i\)', r'friends.getCompound(i).orElseGet(CompoundTag::new)', s)
    s = re.sub(r'upgrades\.getCompound\(i\)', r'upgrades.getCompound(i).orElseGet(CompoundTag::new)', s)
    screen_data.write_text(s, encoding="utf-8")

# Direction vector helper signature changed in 26.2.
screen_be = DST / "src/main/java/net/montoyo/wd/entity/ScreenBlockEntity.java"
if screen_be.exists():
    s = screen_be.read_text(encoding="utf-8")
    s = s.replace(
        "Direction.getNearest(look.x, look.y, look.z).getOpposite()",
        "Direction.getApproximateNearest(look.x, look.y, look.z).getOpposite()"
    )
    screen_be.write_text(s, encoding="utf-8")


# Current resource metadata.
(DST / "src/main/resources/pack.mcmeta").write_text("""{
  "pack": {
    "description": "WebDisplays resources",
    "min_format": 81,
    "max_format": 81
  }
}
""", encoding="utf-8")

print("Prepared", DST)
