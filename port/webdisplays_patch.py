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
    s = s.replace("net.minecraft.advancements.critereon.", "net.minecraft.advancements.criterion.")

    # Block interaction API collapsed back to InteractionResult in 26.2.
    s = s.replace("import net.minecraft.world.ItemInteractionResult;\\n", "")
    s = s.replace("import net.minecraft.world.InteractionResultHolder;\\n", "")
    s = re.sub(r"\\bItemInteractionResult\\b", "InteractionResult", s)
    s = re.sub(r"\\bInteractionResultHolder<\\s*ItemStack\\s*>\\b", "InteractionResult", s)
    s = re.sub(r"InteractionResultHolder\\.success\\([^)]*\\)", "InteractionResult.SUCCESS", s)
    s = re.sub(r"InteractionResultHolder\\.pass\\([^)]*\\)", "InteractionResult.PASS", s)
    s = re.sub(r"InteractionResultHolder\\.consume\\([^)]*\\)", "InteractionResult.CONSUME", s)

    # DirectionProperty was folded into EnumProperty<Direction>.
    s = s.replace("import net.minecraft.world.level.block.state.properties.DirectionProperty;\\n",
                  "import net.minecraft.world.level.block.state.properties.EnumProperty;\\n")
    s = re.sub(r"\\bDirectionProperty\\b", "EnumProperty<Direction>", s)

    # Model/render package moves in 26.2.
    s = s.replace("import net.minecraft.client.renderer.block.model.BakedQuad;",
                  "import net.minecraft.client.resources.model.geometry.BakedQuad;")
    s = s.replace("import net.minecraft.client.resources.model.Material;",
                  "import net.minecraft.client.resources.model.sprite.Material;")
    s = s.replace("import net.minecraft.client.resources.model.ModelState;",
                  "import net.minecraft.client.renderer.block.dispatch.ModelState;")
    s = s.replace("import net.minecraft.world.level.BlockAndTintGetter;",
                  "import net.minecraft.client.renderer.block.BlockAndTintGetter;")
    s = s.replace("import net.minecraft.client.renderer.block.model.ItemTransforms;",
                  "import net.minecraft.client.resources.model.cuboid.ItemTransforms;")

    # 26.2 keeps the same semantic constants on InteractionResult.
    if "InteractionResult " in s and "import net.minecraft.world.InteractionResult;" not in s:
        pkg_end = s.find("\\n", s.find("package "))
        s = s[:pkg_end+1] + "import net.minecraft.world.InteractionResult;\\n" + s[pkg_end+1:]

    java.write_text(s, encoding="utf-8")


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
