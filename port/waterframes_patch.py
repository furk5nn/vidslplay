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
