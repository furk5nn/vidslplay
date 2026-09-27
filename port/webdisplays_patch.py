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
