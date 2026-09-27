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
    s = s.replace("EnumProperty<Direction>.create(", "EnumProperty.create(")

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

# Remove old hand-render/highlight hooks that use APIs removed in 26.2.
# Use brace matching, not regex, because these methods contain nested blocks.
def remove_java_method(source: str, signature: str) -> str:
    sig = source.find(signature)
    if sig < 0:
        return source
    start = source.rfind("\n", 0, sig)
    if start < 0:
        start = 0
    ann_start = source.rfind("\n", 0, start)
    if ann_start >= 0 and "@SubscribeEvent" in source[ann_start:start]:
        start = ann_start
    brace = source.find("{", sig)
    if brace < 0:
        return source
    depth = 0
    i = brace
    while i < len(source):
        ch = source[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                while end < len(source) and source[end] in " \t":
                    end += 1
                if end < len(source) and source[end] == "\r":
                    end += 1
                if end < len(source) and source[end] == "\n":
                    end += 1
                return source[:start] + "\n" + source[end:]
        i += 1
    raise RuntimeError(f"Unbalanced Java method while removing: {signature}")

client_proxy = DST / "src/main/java/net/montoyo/wd/client/ClientProxy.java"
if client_proxy.exists():
    s = client_proxy.read_text(encoding="utf-8")
    s = s.replace("import com.mojang.blaze3d.platform.GlStateManager;", "import com.mojang.blaze3d.opengl.GlStateManager;")
    s = s.replace("import net.neoforged.neoforge.client.event.RenderHighlightEvent;\n", "")
    s = s.replace("import net.neoforged.neoforge.client.event.RenderHandEvent;\n", "")
    s = remove_java_method(s, "public void onRenderPlayerHand(RenderHandEvent ev)")
    s = remove_java_method(s, "public static void onDrawSelection(RenderHighlightEvent.Block event)")
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



# Full 26.2 persistence port for the WebDisplays screen graph.
screen_data = DST / "src/main/java/net/montoyo/wd/entity/ScreenData.java"
if screen_data.exists():
    s = screen_data.read_text(encoding="utf-8")
    s = s.replace("import net.minecraft.core.HolderLookup;\n", "")
    s = s.replace("import net.minecraft.nbt.CompoundTag;\n", "")
    s = s.replace("import net.minecraft.nbt.ListTag;\n", "")
    if "import net.minecraft.core.UUIDUtil;" not in s:
        s = s.replace("import net.minecraft.core.Direction;\n", "import net.minecraft.core.Direction;\nimport net.minecraft.core.UUIDUtil;\n")
    if "import net.minecraft.world.level.storage.ValueInput;" not in s:
        s = s.replace("import net.minecraft.world.level.Level;\n",
                      "import net.minecraft.world.level.Level;\nimport net.minecraft.world.level.storage.ValueInput;\nimport net.minecraft.world.level.storage.ValueOutput;\n")

    start = s.index("    public static ScreenData deserialize(")
    end = s.index("    public int rightsFor(", start)
    methods = r'''    public static ScreenData deserialize(ValueInput input) {
        ScreenData ret = new ScreenData();

        int sideIndex = Byte.toUnsignedInt(input.getByteOr("Side", (byte) 0));
        int rotationIndex = Byte.toUnsignedInt(input.getByteOr("Rotation", (byte) 0));
        ret.side = BlockSide.values()[Math.min(sideIndex, BlockSide.values().length - 1)];
        ret.size = new Vector2i(
                Math.max(1, input.getIntOr("Width", 1)),
                Math.max(1, input.getIntOr("Height", 1))
        );
        ret.resolution = new Vector2i(
                input.getIntOr("ResolutionX", 0),
                input.getIntOr("ResolutionY", 0)
        );
        ret.rotation = Rotation.values()[Math.min(rotationIndex, Rotation.values().length - 1)];
        ret.url = input.getStringOr("URL", "");
        ret.videoType = VideoType.getTypeFromURL(ret.url);

        if (ret.resolution.x <= 0 || ret.resolution.y <= 0) {
            float psx = ((float) ret.size.x) * 16.f - 4.f;
            float psy = ((float) ret.size.y) * 16.f - 4.f;
            ret.resolution.x = (int) (psx * 8.f);
            ret.resolution.y = (int) (psy * 8.f);
        }

        String ownerName = input.getStringOr("OwnerName", "");
        UUID ownerUuid = input.read("OwnerUUID", UUIDUtil.CODEC).orElse(null);
        if (!ownerName.isEmpty() && ownerUuid != null) {
            ret.owner = new NameUUIDPair(ownerName, ownerUuid);
        }

        ret.friends = new ArrayList<>();
        for (ValueInput friend : input.childrenListOrEmpty("Friends")) {
            String name = friend.getStringOr("Name", "");
            UUID uuid = friend.read("UUID", UUIDUtil.CODEC).orElse(null);
            if (uuid != null) ret.friends.add(new NameUUIDPair(name, uuid));
        }

        ret.friendRights = Byte.toUnsignedInt(input.getByteOr("FriendRights", (byte) 0));
        ret.otherRights = Byte.toUnsignedInt(input.getByteOr("OtherRights", (byte) 0));

        ret.upgrades = new ArrayList<>();
        for (ItemStack stack : input.listOrEmpty("Upgrades", ItemStack.CODEC)) {
            if (!stack.isEmpty()) ret.upgrades.add(stack);
        }

        ret.autoVolume = input.getBooleanOr("AutoVolume", true);
        ret.ownerVolume = Math.max(0, Math.min(100, input.getIntOr("OwnerVolume", 100)));
        ret.userSyncEnabled = input.getBooleanOr("SyncEnabled", false);
        ret.syncMasterUUID = input.read("SyncMaster", UUIDUtil.CODEC).orElse(null);
        ret.syncPlaybackTime = input.getDoubleOr("SyncTime", 0.0);
        ret.syncPaused = input.getBooleanOr("SyncPaused", false);
        ret.syncUpdateTimestamp = input.getLongOr("SyncTs", 0L);
        return ret;
    }

    public void serialize(ValueOutput output) {
        output.putByte("Side", (byte) side.ordinal());
        output.putInt("Width", size.x);
        output.putInt("Height", size.y);
        output.putInt("ResolutionX", resolution.x);
        output.putInt("ResolutionY", resolution.y);
        output.putByte("Rotation", (byte) rotation.ordinal());
        output.putString("URL", url == null ? "" : url);

        if (owner == null) {
            Log.warning("Found TES with NO OWNER!!");
        } else {
            output.putString("OwnerName", owner.name);
            output.store("OwnerUUID", UUIDUtil.CODEC, owner.uuid);
        }

        ValueOutput.ValueOutputList friendList = output.childrenList("Friends");
        for (NameUUIDPair f : friends) {
            ValueOutput friend = friendList.addChild();
            friend.putString("Name", f.name);
            friend.store("UUID", UUIDUtil.CODEC, f.uuid);
        }

        output.putByte("FriendRights", (byte) friendRights);
        output.putByte("OtherRights", (byte) otherRights);

        ValueOutput.TypedOutputList<ItemStack> upgradeList = output.list("Upgrades", ItemStack.CODEC);
        for (ItemStack stack : upgrades) {
            if (!stack.isEmpty()) upgradeList.add(stack);
        }

        output.putBoolean("AutoVolume", autoVolume);
        output.putInt("OwnerVolume", ownerVolume);
        output.putBoolean("SyncEnabled", userSyncEnabled);
        if (syncMasterUUID != null) output.store("SyncMaster", UUIDUtil.CODEC, syncMasterUUID);
        output.putDouble("SyncTime", syncPlaybackTime);
        output.putBoolean("SyncPaused", syncPaused);
        output.putLong("SyncTs", syncUpdateTimestamp);
    }

'''
    s = s[:start] + methods + s[end:]
    screen_data.write_text(s, encoding="utf-8")

screen_be = DST / "src/main/java/net/montoyo/wd/entity/ScreenBlockEntity.java"
if screen_be.exists():
    s = screen_be.read_text(encoding="utf-8")
    s = s.replace("import net.minecraft.nbt.ListTag;\n", "")
    s = s.replace("import net.minecraft.nbt.Tag;\n", "")
    if "import net.minecraft.core.HolderLookup;" not in s:
        s = s.replace("import net.minecraft.core.Direction;\n", "import net.minecraft.core.Direction;\nimport net.minecraft.core.HolderLookup;\n")
    if "import net.minecraft.world.level.storage.ValueInput;" not in s:
        s = s.replace("import net.minecraft.world.level.block.state.BlockState;\n",
                      "import net.minecraft.world.level.block.state.BlockState;\nimport net.minecraft.world.level.storage.ValueInput;\nimport net.minecraft.world.level.storage.ValueOutput;\n")

    load_start = s.index("    @Override\n    protected void loadAdditional(")
    after_save = s.index("    public ScreenData addScreen(", load_start)
    persistence = r'''    @Override
    protected void loadAdditional(ValueInput input) {
        super.loadAdditional(input);

        for (ScreenData screen : screens) {
            if (screen.browser != null) {
                screen.browser.close(true);
                screen.browser = null;
            }
        }

        screens.clear();
        for (ValueInput child : input.childrenListOrEmpty("WDScreens")) {
            screens.add(ScreenData.deserialize(child));
        }
        loaded = false;
        updateAABB();
    }

    @Override
    protected void saveAdditional(ValueOutput output) {
        super.saveAdditional(output);
        ValueOutput.ValueOutputList list = output.childrenList("WDScreens");
        for (ScreenData screen : screens) {
            screen.serialize(list.addChild());
        }
    }

    @Override
    public CompoundTag getUpdateTag(HolderLookup.Provider registries) {
        return saveCustomOnly(registries);
    }

    @Override
    public void handleUpdateTag(ValueInput input) {
        super.handleUpdateTag(input);
        for (ScreenData screen : screens) {
            if (screen.browser == null) screen.createBrowser(this, false);
            if (screen.browser != null) screen.browser.loadURL(screen.url);
        }
        updateAABB();
    }

'''
    s = s[:load_start] + persistence + s[after_save:]
    screen_be.write_text(s, encoding="utf-8")

peripheral = DST / "src/main/java/net/montoyo/wd/entity/AbstractPeripheralBlockEntity.java"
if peripheral.exists():
    s = peripheral.read_text(encoding="utf-8")
    s = s.replace("import net.minecraft.core.HolderLookup;\n", "")
    s = s.replace("import net.minecraft.nbt.CompoundTag;\n", "")
    if "import net.minecraft.world.level.storage.ValueInput;" not in s:
        s = s.replace("import net.minecraft.world.level.chunk.LevelChunk;\n",
                      "import net.minecraft.world.level.chunk.LevelChunk;\nimport net.minecraft.world.level.storage.ValueInput;\nimport net.minecraft.world.level.storage.ValueOutput;\n")

    start = s.index("    @Override\n    protected void loadAdditional(")
    end = s.index("    @Override\n    public boolean connect(", start)
    methods = r'''    @Override
    protected void loadAdditional(ValueInput input) {
        super.loadAdditional(input);
        var child = input.child("WDScreen");
        if (child.isPresent()) {
            ValueInput screen = child.get();
            screenPos = new Vector3i(
                    screen.getIntOr("X", 0),
                    screen.getIntOr("Y", 0),
                    screen.getIntOr("Z", 0)
            );
            int side = Byte.toUnsignedInt(screen.getByteOr("Side", (byte) 0));
            screenSide = BlockSide.values()[Math.min(side, BlockSide.values().length - 1)];
        } else {
            screenPos = null;
            screenSide = null;
        }
    }

    @Override
    protected void saveAdditional(ValueOutput output) {
        super.saveAdditional(output);
        if (screenPos != null && screenSide != null) {
            ValueOutput screen = output.child("WDScreen");
            screen.putInt("X", screenPos.x);
            screen.putInt("Y", screenPos.y);
            screen.putInt("Z", screenPos.z);
            screen.putByte("Side", (byte) screenSide.ordinal());
        }
    }

'''
    s = s[:start] + methods + s[end:]
    peripheral.write_text(s, encoding="utf-8")



# Repair generic static factory calls produced by the DirectionProperty migration.
for java in (DST / "src/main/java").rglob("*.java"):
    s = java.read_text(encoding="utf-8")
    s = s.replace("EnumProperty<Direction>.create(", "EnumProperty.create(")
    java.write_text(s, encoding="utf-8")

# Remove obsolete event methods without regexing across nested blocks.
def remove_java_method(source: str, signature_fragment: str) -> str:
    pos = source.find(signature_fragment)
    if pos < 0:
        return source

    line_start = source.rfind("\n", 0, pos) + 1
    # Include immediately preceding annotations.
    scan = line_start
    while scan > 0:
        prev_end = scan - 1
        prev_start = source.rfind("\n", 0, prev_end) + 1
        prev = source[prev_start:prev_end].strip()
        if prev.startswith("@"):
            line_start = prev_start
            scan = prev_start
        else:
            break

    brace = source.find("{", pos)
    if brace < 0:
        return source

    depth = 0
    i = brace
    in_string = False
    string_quote = ""
    escaped = False
    while i < len(source):
        ch = source[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == string_quote:
                in_string = False
        else:
            if ch in ('"', "'"):
                in_string = True
                string_quote = ch
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    if end < len(source) and source[end] == "\n":
                        end += 1
                    return source[:line_start] + source[end:]
        i += 1
    return source

client_proxy = DST / "src/main/java/net/montoyo/wd/client/ClientProxy.java"
if client_proxy.exists():
    # Start from the upstream copy again for this file so no earlier partial
    # regex deletion can leave unmatched braces.
    upstream_client_proxy = SRC / "src/main/java/net/montoyo/wd/client/ClientProxy.java"
    s = upstream_client_proxy.read_text(encoding="utf-8")

    s = s.replace("import net.minecraft.resources.ResourceLocation;", "import net.minecraft.resources.Identifier;")
    s = re.sub(r"\bResourceLocation\b", "Identifier", s)
    s = s.replace("import net.minecraft.Util;", "import net.minecraft.util.Util;")
    s = s.replace("import com.mojang.blaze3d.platform.GlStateManager;", "import com.mojang.blaze3d.opengl.GlStateManager;")
    s = s.replace("import net.neoforged.neoforge.client.event.ModelEvent;\n", "")
    s = s.replace("import net.neoforged.neoforge.client.event.RenderHighlightEvent;\n", "")
    s = s.replace("import net.montoyo.wd.client.renderers.ScreenModelLoader;\n", "")
    s = s.replace("import net.montoyo.wd.client.renderers.ScreenThinModelLoader;\n", "")
    s = re.sub(r"\.isClientSide\b(?!\s*\()", ".isClientSide()", s)
    s = s.replace(".isClientSide()()", ".isClientSide()")

    s = remove_java_method(s, "public static void onModelRegistryEvent(")
    s = remove_java_method(s, "public void onRenderPlayerHand(")
    s = remove_java_method(s, "public static void onDrawSelection(")

    client_proxy.write_text(s, encoding="utf-8")


# 26.2 browser-texture bridge. MCEF owns the native GL texture; Minecraft only
# gets a non-owning GpuTexture view so the normal submit pipeline can sample it.
render_dir = DST / "src/main/java/net/montoyo/wd/client/renderers"
(render_dir / "BrowserTextureBridge.java").write_text("""package net.montoyo.wd.client.renderers;

import com.cinemamod.mcef.MCEFBrowser;
import com.mojang.blaze3d.GpuFormat;
import com.mojang.blaze3d.opengl.FrameBufferCache;
import com.mojang.blaze3d.opengl.GlTexture;
import com.mojang.blaze3d.systems.RenderSystem;
import com.mojang.blaze3d.textures.FilterMode;
import com.mojang.blaze3d.textures.GpuTexture;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.texture.AbstractTexture;
import net.minecraft.resources.Identifier;

import java.util.WeakHashMap;

final class BrowserTextureBridge {
    private static final WeakHashMap<MCEFBrowser, Entry> ENTRIES = new WeakHashMap<>();

    private BrowserTextureBridge() {}

    static Identifier texture(MCEFBrowser browser, int width, int height) {
        if (browser == null || browser.getRenderer() == null) return null;
        int nativeId = browser.getRenderer().getTextureID();
        if (nativeId <= 0) return null;

        Entry old = ENTRIES.get(browser);
        if (old != null && old.nativeId == nativeId) return old.identifier;

        Minecraft mc = Minecraft.getInstance();
        if (old != null) mc.getTextureManager().release(old.identifier);

        Identifier identifier = Identifier.fromNamespaceAndPath(
                "webdisplays",
                "mcef/screen_" + Integer.toUnsignedString(System.identityHashCode(browser))
        );
        ExternalTexture texture = new ExternalTexture(nativeId, Math.max(1, width), Math.max(1, height));
        mc.getTextureManager().register(identifier, texture);
        ENTRIES.put(browser, new Entry(nativeId, identifier));
        return identifier;
    }

    private record Entry(int nativeId, Identifier identifier) {}

    private static final class ExternalTexture extends AbstractTexture {
        ExternalTexture(int nativeId, int width, int height) {
            ForeignGlTexture foreign = new ForeignGlTexture(nativeId, width, height);
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
    }

    private static final class ForeignGlTexture extends GlTexture {
        private static final FrameBufferCache FRAMEBUFFER_CACHE = new FrameBufferCache();
        private boolean disposed;

        ForeignGlTexture(int nativeId, int width, int height) {
            super(
                    GpuTexture.USAGE_TEXTURE_BINDING,
                    "webdisplays-mcef-screen",
                    GpuFormat.RGBA8_UNORM,
                    width,
                    height,
                    1,
                    1,
                    nativeId,
                    FRAMEBUFFER_CACHE
            );
        }

        @Override
        public void close() {
            // Native texture belongs to MCEF.
            disposed = true;
        }

        @Override
        public boolean isClosed() {
            return disposed;
        }
    }
}
""", encoding="utf-8")

# Full 26.2 state/extract/submit screen renderer.
(render_dir / "ScreenRenderer.java").write_text("""package net.montoyo.wd.client.renderers;

import com.cinemamod.mcef.MCEFBrowser;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderer;
import net.minecraft.client.renderer.blockentity.BlockEntityRendererProvider;
import net.minecraft.client.renderer.blockentity.state.BlockEntityRenderState;
import net.minecraft.client.renderer.feature.ModelFeatureRenderer;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.state.level.CameraRenderState;
import net.minecraft.resources.Identifier;
import net.minecraft.world.phys.Vec3;
import net.montoyo.wd.WebDisplays;
import net.montoyo.wd.config.ClientConfig;
import net.montoyo.wd.entity.ScreenBlockEntity;
import net.montoyo.wd.entity.ScreenData;
import net.montoyo.wd.utilities.data.BlockSide;
import org.jspecify.annotations.Nullable;

import java.util.ArrayList;
import java.util.List;

import static com.mojang.math.Axis.*;

public final class ScreenRenderer implements BlockEntityRenderer<ScreenBlockEntity, ScreenRenderer.State> {
    public ScreenRenderer(BlockEntityRendererProvider.Context context) {}

    public static final class State extends BlockEntityRenderState {
        final List<Entry> entries = new ArrayList<>();
    }

    private record Entry(
            BlockSide side,
            int width,
            int height,
            float rotation,
            float turnOnScale,
            Identifier texture,
            float brightness
    ) {}

    @Override
    public State createRenderState() {
        return new State();
    }

    @Override
    public void extractRenderState(
            ScreenBlockEntity be,
            State state,
            float partialTick,
            Vec3 cameraPosition,
            ModelFeatureRenderer.@Nullable CrumblingOverlay breakProgress) {
        BlockEntityRenderer.super.extractRenderState(be, state, partialTick, cameraPosition, breakProgress);
        state.entries.clear();
        if (!be.isLoaded()) return;

        for (int i = 0; i < be.screenCount(); i++) {
            ScreenData screen = be.getScreen(i);

            if (screen.browser == null) {
                double distance = WebDisplays.PROXY.distanceTo(be, cameraPosition);
                if (distance <= WebDisplays.INSTANCE.loadDistance2) {
                    screen.createBrowser(be, true);
                }
            }

            if (!(screen.browser instanceof MCEFBrowser browser)) continue;
            if (browser.getRenderer() == null || browser.getRenderer().getTextureID() <= 0) continue;

            Identifier texture = BrowserTextureBridge.texture(
                    browser,
                    screen.rotation.isVertical ? screen.resolution.y : screen.resolution.x,
                    screen.rotation.isVertical ? screen.resolution.x : screen.resolution.y
            );
            if (texture == null) continue;

            float scale = 1.0f;
            if (screen.doTurnOnAnim) {
                scale = Math.min(1.0f, Math.max(0.0f,
                        (System.currentTimeMillis() - screen.turnOnTime) / 100.0f));
                if (scale >= 1.0f) screen.doTurnOnAnim = false;
            }

            state.entries.add(new Entry(
                    screen.side,
                    screen.size.x,
                    screen.size.y,
                    screen.rotation.angle,
                    scale,
                    texture,
                    (float) ClientConfig.screenBrightness
            ));
        }
    }

    @Override
    public void submit(State state, PoseStack poseStack, SubmitNodeCollector collector, CameraRenderState camera) {
        for (Entry entry : state.entries) {
            submitEntry(entry, poseStack, collector);
        }
    }

    private static void submitEntry(Entry entry, PoseStack poseStack, SubmitNodeCollector collector) {
        BlockSide side = entry.side();

        float mx = 0.5f + (side.right.x * entry.width()) * 0.5f
                           + (side.up.x * entry.height()) * 0.5f
                           + side.left.x * 0.5f
                           + side.down.x * 0.5f;
        float my = 0.5f + (side.right.y * entry.width()) * 0.5f
                           + (side.up.y * entry.height()) * 0.5f
                           + side.left.y * 0.5f
                           + side.down.y * 0.5f;
        float mz = 0.5f + (side.right.z * entry.width()) * 0.5f
                           + (side.up.z * entry.height()) * 0.5f
                           + side.left.z * 0.5f
                           + side.down.z * 0.5f;

        poseStack.pushPose();
        poseStack.translate(mx, my, mz);

        switch (side) {
            case BOTTOM -> poseStack.mulPose(XP.rotationDegrees(139.8f));
            case TOP -> poseStack.mulPose(XN.rotationDegrees(139.8f));
            case NORTH -> poseStack.mulPose(YN.rotationDegrees(180.0f));
            case SOUTH -> {}
            case WEST -> poseStack.mulPose(YN.rotationDegrees(90.0f));
            case EAST -> poseStack.mulPose(YP.rotationDegrees(90.0f));
        }

        if (entry.turnOnScale() < 1.0f) {
            poseStack.scale(entry.turnOnScale(), entry.turnOnScale(), 1.0f);
        }
        if (entry.rotation() != 0.0f) {
            poseStack.mulPose(ZP.rotationDegrees(entry.rotation()));
        }

        float sw = entry.width() * 0.5f - 2.0f / 16.0f;
        float sh = entry.height() * 0.5f - 2.0f / 16.0f;
        boolean vertical = Math.abs(entry.rotation()) == 90.0f || Math.abs(entry.rotation()) == 270.0f;
        if (vertical) {
            float tmp = sw;
            sw = sh;
            sh = tmp;
        }

        final float halfW = sw;
        final float halfH = sh;
        final float brightness = entry.brightness();

        collector.submitCustomGeometry(
                poseStack,
                RenderTypes.entityTranslucent(entry.texture()),
                (pose, builder) -> emitScreen(pose, builder, halfW, halfH, brightness)
        );
        poseStack.popPose();
    }

    private static void emitScreen(
            PoseStack.Pose pose,
            VertexConsumer builder,
            float sw,
            float sh,
            float brightness) {
        int c = Math.max(0, Math.min(255, Math.round(brightness * 255.0f)));
        builder.addVertex(pose, -sw, -sh, 0.505f).setColor(c, c, c, 255).setUv(0.0f, 1.0f);
        builder.addVertex(pose,  sw, -sh, 0.505f).setColor(c, c, c, 255).setUv(1.0f, 1.0f);
        builder.addVertex(pose,  sw,  sh, 0.505f).setColor(c, c, c, 255).setUv(1.0f, 0.0f);
        builder.addVertex(pose, -sw,  sh, 0.505f).setColor(c, c, c, 255).setUv(0.0f, 0.0f);
    }

    @Override
    public boolean shouldRenderOffScreen() {
        return true;
    }

    @Override
    public int getViewDistance() {
        return 256;
    }

    @Override
    public boolean shouldRender(ScreenBlockEntity be, Vec3 cameraPos) {
        return WebDisplays.PROXY.distanceTo(be, cameraPos) <= WebDisplays.INSTANCE.unloadDistance2;
    }
}
""", encoding="utf-8")

stage = render_dir / "ScreenStageRenderer.java"
if stage.exists():
    stage.unlink()

# Register the 26.2 renderer provider directly.
client_proxy = DST / "src/main/java/net/montoyo/wd/client/ClientProxy.java"
if client_proxy.exists():
    s = client_proxy.read_text(encoding="utf-8")
    s = s.replace(
        "BlockEntityRenderers.register(TileRegistry.SCREEN_BLOCK_ENTITY.get(), new ScreenRenderer.ScreenRendererProvider());",
        "BlockEntityRenderers.register(TileRegistry.SCREEN_BLOCK_ENTITY.get(), ScreenRenderer::new);"
    )
    client_proxy.write_text(s, encoding="utf-8")


# Client-only local media registry. Paths never leave the client and are not
# serialized into world/chunk data.
client_dir = DST / "src/main/java/net/montoyo/wd/client"
(client_dir / "LocalMediaManager.java").write_text("""package net.montoyo.wd.client;

import me.srrapero720.waterframes.api.LocalMediaPlayer;
import net.minecraft.resources.Identifier;
import net.minecraft.world.level.Level;
import net.montoyo.wd.entity.ScreenBlockEntity;
import net.montoyo.wd.entity.ScreenData;
import net.montoyo.wd.utilities.data.BlockSide;

import java.io.File;
import java.util.HashMap;
import java.util.IdentityHashMap;
import java.util.Map;

public final class LocalMediaManager {
    public static final LocalMediaManager INSTANCE = new LocalMediaManager();

    private final Map<Level, Map<Key, LocalMediaPlayer>> players = new IdentityHashMap<>();

    private LocalMediaManager() {}

    public synchronized void open(ScreenBlockEntity blockEntity, BlockSide side, File file) throws Exception {
        Level level = blockEntity.getLevel();
        if (level == null) throw new IllegalStateException("Screen is not in a level");

        Key key = new Key(blockEntity.getBlockPos().asLong(), side.ordinal());
        Map<Key, LocalMediaPlayer> levelPlayers = players.computeIfAbsent(level, ignored -> new HashMap<>());

        LocalMediaPlayer old = levelPlayers.remove(key);
        if (old != null) old.close();

        ScreenData screen = blockEntity.getScreen(side);
        if (screen != null && screen.browser != null) {
            screen.browser.close(true);
            screen.browser = null;
        }

        levelPlayers.put(key, new LocalMediaPlayer(file.getCanonicalFile().toURI()));
    }

    public synchronized Identifier texture(ScreenBlockEntity blockEntity, BlockSide side) {
        LocalMediaPlayer player = player(blockEntity, side);
        return player == null ? null : player.texture();
    }

    public synchronized boolean has(ScreenBlockEntity blockEntity, BlockSide side) {
        return player(blockEntity, side) != null;
    }

    public synchronized boolean isLoading(ScreenBlockEntity blockEntity, BlockSide side) {
        LocalMediaPlayer player = player(blockEntity, side);
        return player != null && player.isLoading();
    }

    public synchronized void clear(ScreenBlockEntity blockEntity, BlockSide side) {
        Level level = blockEntity.getLevel();
        if (level == null) return;
        Map<Key, LocalMediaPlayer> levelPlayers = players.get(level);
        if (levelPlayers == null) return;
        LocalMediaPlayer player = levelPlayers.remove(new Key(blockEntity.getBlockPos().asLong(), side.ordinal()));
        if (player != null) player.close();
        if (levelPlayers.isEmpty()) players.remove(level);
    }

    public synchronized void clearLevel(Level level) {
        Map<Key, LocalMediaPlayer> levelPlayers = players.remove(level);
        if (levelPlayers == null) return;
        for (LocalMediaPlayer player : levelPlayers.values()) player.close();
        levelPlayers.clear();
    }

    private LocalMediaPlayer player(ScreenBlockEntity blockEntity, BlockSide side) {
        Level level = blockEntity.getLevel();
        if (level == null) return null;
        Map<Key, LocalMediaPlayer> levelPlayers = players.get(level);
        return levelPlayers == null ? null : levelPlayers.get(new Key(blockEntity.getBlockPos().asLong(), side.ordinal()));
    }

    private record Key(long pos, int side) {}
}
""", encoding="utf-8")

# Existing Shift+right-click Set URL GUI gets one extra button, nothing else is
# replaced or moved.
gui = DST / "src/main/java/net/montoyo/wd/client/gui/GuiSetURL2.java"
if gui.exists():
    s = gui.read_text(encoding="utf-8")
    s = s.replace("import net.montoyo.wd.client.ClientProxy;", "import net.montoyo.wd.client.ClientProxy;\nimport net.montoyo.wd.client.LocalMediaManager;")
    if "org.lwjgl.util.tinyfd.TinyFileDialogs" not in s:
        s = s.replace("import java.io.IOException;", "import java.io.IOException;\nimport java.io.File;\nimport org.lwjgl.util.tinyfd.TinyFileDialogs;")

    s = s.replace(
        "\\t@FillControl\\n\\tprivate Button btnOk;",
        "\\t@FillControl\\n\\tprivate Button btnOk;\\n\\n\\t@FillControl\\n\\tprivate Button btnLocalFile;"
    )

    old = """\t\telse if (ev.getSource() == btnOk)
\t\t\tvalidate(tfURL.getText());
\t\telse if (ev.getSource() == btnShutDown) {"""
    new = """\t\telse if (ev.getSource() == btnOk)
\t\t\tvalidate(tfURL.getText());
\t\telse if (ev.getSource() == btnLocalFile && !isPad) {
\t\t\tString selected = TinyFileDialogs.tinyfd_openFileDialog(
\t\t\t\t\t"Choose local MP4",
\t\t\t\t\t"",
\t\t\t\t\tnew String[]{"*.mp4"},
\t\t\t\t\t"MP4 video",
\t\t\t\t\tfalse
\t\t\t);
\t\t\tif (selected != null && !selected.isBlank()) {
\t\t\t\ttry {
\t\t\t\t\tFile file = new File(selected);
\t\t\t\t\tif (!file.isFile() || !file.getName().toLowerCase(java.util.Locale.ROOT).endsWith(".mp4"))
\t\t\t\t\t\tthrow new IOException("Please choose an .mp4 file");
\t\t\t\t\tLocalMediaManager.INSTANCE.open(tileEntity, screenSide, file);
\t\t\t\t\tminecraft.setScreen(null);
\t\t\t\t} catch (Exception ex) {
\t\t\t\t\tthrow new RuntimeException("Could not open local video", ex);
\t\t\t\t}
\t\t\t}
\t\t}
\t\telse if (ev.getSource() == btnShutDown) {"""
    s = s.replace(old, new)

    # Returning to a normal URL cleanly shuts down the local WaterFrames player.
    s = s.replace(
        "\\tprivate void validate(String url) {\\n\\t\\tif (!url.isEmpty()) {",
        "\\tprivate void validate(String url) {\\n\\t\\tif (!isPad && tileEntity != null) LocalMediaManager.INSTANCE.clear(tileEntity, screenSide);\\n\\t\\tif (!url.isEmpty()) {"
    )
    gui.write_text(s, encoding="utf-8")

# Add the button under the existing URL field. Preserve the original GUI and
# its OK/Cancel layout, merely shift that row down.
gui_json = DST / "src/main/resources/assets/webdisplays/gui/seturl.json"
gui_json.write_text("""{
  "controls": [
    {
      "type": "Label",
      "label": "$webdisplays.gui.seturl.url",
      "x": 0,
      "y": 0,
      "shadowed": true
    },
    {
      "type": "TextField",
      "name": "tfURL",
      "x": 0,
      "y": 12,
      "width": 272,
      "maxLength": 65535
    },
    {
      "type": "YTButton",
      "x": 276,
      "y": 13,
      "width": 20,
      "urlField": "tfURL"
    },
    {
      "type": "Button",
      "name": "btnLocalFile",
      "label": "Yerel Dosya...",
      "x": 0,
      "y": 38,
      "width": 296,
      "visible": "1 - isPad",
      "disabled": "isPad"
    },
    {
      "type": "Button",
      "name": "btnShutDown",
      "label": "$webdisplays.gui.seturl.shutdown",
      "x": 0,
      "y": "isPad & 38 | 66",
      "width": 96,
      "visible": "isPad",
      "disabled": "1 - isPad"
    },
    {
      "type": "Button",
      "name": "btnCancel",
      "label": "$webdisplays.gui.seturl.cancel",
      "x": "isPad & 100 | 0",
      "y": "isPad & 38 | 66",
      "width": "isPad & 96 | 146"
    },
    {
      "type": "Button",
      "name": "btnOk",
      "label": "$webdisplays.gui.seturl.ok",
      "x": "isPad & 200 | 150",
      "y": "isPad & 38 | 66",
      "width": "isPad & 96 | 146"
    }
  ],
  "center": true
}
""", encoding="utf-8")

# Prefer a local WaterFrames texture over MCEF for that exact screen side.
renderer = render_dir / "ScreenRenderer.java"
if renderer.exists():
    s = renderer.read_text(encoding="utf-8")
    s = s.replace(
        "import net.montoyo.wd.config.ClientConfig;",
        "import net.montoyo.wd.config.ClientConfig;\nimport net.montoyo.wd.client.LocalMediaManager;"
    )
    old = """            if (screen.browser == null) {
                double distance = WebDisplays.PROXY.distanceTo(be, cameraPosition);
                if (distance <= WebDisplays.INSTANCE.loadDistance2) {
                    screen.createBrowser(be, true);
                }
            }

            if (!(screen.browser instanceof MCEFBrowser browser)) continue;
            if (browser.getRenderer() == null || browser.getRenderer().getTextureID() <= 0) continue;

            Identifier texture = BrowserTextureBridge.texture(
                    browser,
                    screen.rotation.isVertical ? screen.resolution.y : screen.resolution.x,
                    screen.rotation.isVertical ? screen.resolution.x : screen.resolution.y
            );
            if (texture == null) continue;"""
    new = """            Identifier texture;
            if (LocalMediaManager.INSTANCE.has(be, screen.side)) {
                texture = LocalMediaManager.INSTANCE.texture(be, screen.side);
                if (texture == null) continue;
            } else {
                if (screen.browser == null) {
                    double distance = WebDisplays.PROXY.distanceTo(be, cameraPosition);
                    if (distance <= WebDisplays.INSTANCE.loadDistance2) {
                        screen.createBrowser(be, true);
                    }
                }

                if (!(screen.browser instanceof MCEFBrowser browser)) continue;
                if (browser.getRenderer() == null || browser.getRenderer().getTextureID() <= 0) continue;

                texture = BrowserTextureBridge.texture(
                        browser,
                        screen.rotation.isVertical ? screen.resolution.y : screen.resolution.x,
                        screen.rotation.isVertical ? screen.resolution.x : screen.resolution.y
                );
                if (texture == null) continue;
            }"""
    s = s.replace(old, new)
    renderer.write_text(s, encoding="utf-8")

# Close client-local players when their world unloads.
client_proxy = DST / "src/main/java/net/montoyo/wd/client/ClientProxy.java"
if client_proxy.exists():
    s = client_proxy.read_text(encoding="utf-8")
    needle = """\tpublic void onWorldUnload(LevelEvent.Unload ev) {
\t\tLog.info("World unloaded; killing screens...");
\t\tif (ev.getLevel() instanceof Level level) {"""
    replacement = """\tpublic void onWorldUnload(LevelEvent.Unload ev) {
\t\tLog.info("World unloaded; killing screens...");
\t\tif (ev.getLevel() instanceof Level level) {
\t\t\tLocalMediaManager.INSTANCE.clearLevel(level);"""
    s = s.replace(needle, replacement)
    client_proxy.write_text(s, encoding="utf-8")

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


# ===========================================================================
# FINAL 26.2 NORMALIZATION PASS
# Run LAST so later source transplants cannot resurrect 1.21.x APIs.
# ===========================================================================
java_root = DST / "src/main/java"
for java in java_root.rglob("*.java"):
    text = java.read_text(encoding="utf-8")

    # Mojang package/name migrations that may have been reintroduced later.
    text = text.replace("import net.minecraft.client.gui.GuiGraphics;", "import net.minecraft.client.gui.GuiGraphicsExtractor;")
    text = re.sub(r"\bGuiGraphics\b", "GuiGraphicsExtractor", text)
    text = text.replace("import com.mojang.blaze3d.platform.GlStateManager;", "import com.mojang.blaze3d.opengl.GlStateManager;")
    text = text.replace("import net.minecraft.Util;", "import net.minecraft.util.Util;")
    text = text.replace("net.minecraft.Util.", "net.minecraft.util.Util.")
    text = text.replace(".dimension().location()", ".dimension().identifier()")

    # Authlib GameProfile is record-style in the 26.x dependency.
    text = text.replace(".getGameProfile().getId()", ".getGameProfile().id()")
    text = text.replace(".getGameProfile().getName()", ".getGameProfile().name()")
    text = re.sub(r"\bprofile\.getId\(\)", "profile.id()", text)
    text = re.sub(r"\bprofile\.getName\(\)", "profile.name()", text)

    # Current screen moved behind Minecraft.gui.
    text = re.sub(r"\bmc\.screen\b", "mc.gui.screen()", text)
    text = re.sub(r"\bminecraft\.screen\b", "minecraft.gui.screen()", text)
    text = text.replace("Minecraft.getInstance().screen", "Minecraft.getInstance().gui.screen()")
    text = re.sub(r"\bmc\.setScreen\(", "mc.gui.setScreen(", text)
    text = re.sub(r"\bminecraft\.setScreen\(", "minecraft.gui.setScreen(", text)
    text = text.replace("Minecraft.getInstance().setScreen(", "Minecraft.getInstance().gui.setScreen(")

    # Modifier state moved to Minecraft.
    text = text.replace("Screen.hasShiftDown()", "Minecraft.getInstance().hasShiftDown()")
    text = text.replace("Screen.hasControlDown()", "Minecraft.getInstance().hasControlDown()")

    # Camera/Window/Inventory 26.2 accessors.
    text = re.sub(r"\bcamera\.getEntity\(\)", "camera.entity()", text)
    text = text.replace("Minecraft.getInstance().getWindow().getWindow()", "Minecraft.getInstance().getWindow()")
    text = text.replace("ep.getInventory().items", "ep.getInventory().getNonEquipmentItems()")

    # NeoForge/FML current loader state.
    text = text.replace("FMLEnvironment.dist", "net.neoforged.fml.loading.FMLLoader.getCurrent().getDist()")
    text = text.replace("FMLEnvironment.production", "net.neoforged.fml.loading.FMLLoader.getCurrent().isProduction()")

    # DirectionProperty migration may have been reintroduced.
    text = text.replace("import net.minecraft.world.level.block.state.properties.DirectionProperty;",
                        "import net.minecraft.world.level.block.state.properties.EnumProperty;")
    text = re.sub(r"\bDirectionProperty\b", "EnumProperty<Direction>", text)
    text = text.replace("EnumProperty<Direction>.create(", "EnumProperty.create(")

    # Old right-click item result type no longer exists.
    text = text.replace("import net.minecraft.world.InteractionResultHolder;\n", "")
    text = re.sub(r"\bInteractionResultHolder<\s*ItemStack\s*>\b", "InteractionResult", text)
    text = re.sub(r"InteractionResultHolder\.success\([^)]*\)", "InteractionResult.SUCCESS", text)
    text = re.sub(r"InteractionResultHolder\.pass\([^)]*\)", "InteractionResult.PASS", text)

    java.write_text(text, encoding="utf-8")


# NeoForge 26.2 EventBusSubscriber no longer takes the old bus selector here.
network = DST / "src/main/java/net/montoyo/wd/net/WDNetworkRegistry.java"
if network.exists():
    text = network.read_text(encoding="utf-8")
    text = re.sub(
        r'@EventBusSubscriber\(\s*modid\s*=\s*"webdisplays"\s*,\s*bus\s*=\s*EventBusSubscriber\.Bus\.MOD\s*\)\s*',
        '',
        text
    )
    network.write_text(text, encoding="utf-8")


# GameProfile pair helper.
pair = DST / "src/main/java/net/montoyo/wd/utilities/serialization/NameUUIDPair.java"
if pair.exists():
    text = pair.read_text(encoding="utf-8")
    text = text.replace("profile.getName()", "profile.name()")
    text = text.replace("profile.getId()", "profile.id()")
    pair.write_text(text, encoding="utf-8")


# Persistence owner helpers: retain CompoundTag overloads for packet/custom-data
# use and add ValueInput/ValueOutput overloads for block-entity persistence.
util = DST / "src/main/java/net/montoyo/wd/utilities/serialization/Util.java"
if util.exists():
    text = util.read_text(encoding="utf-8")
    if "import net.minecraft.world.level.storage.ValueInput;" not in text:
        text = text.replace(
            "import net.minecraft.nbt.CompoundTag;",
            "import net.minecraft.nbt.CompoundTag;\nimport net.minecraft.world.level.storage.ValueInput;\nimport net.minecraft.world.level.storage.ValueOutput;"
        )
    text = text.replace('long msb = tag.getLong("OwnerMSB");', 'long msb = tag.getLongOr("OwnerMSB", 0L);')
    text = text.replace('long lsb = tag.getLong("OwnerLSB");', 'long lsb = tag.getLongOr("OwnerLSB", 0L);')
    text = text.replace('String str = tag.getString("OwnerName");', 'String str = tag.getStringOr("OwnerName", "");')
    if "writeOwnerToNBT(ValueOutput" not in text:
        insert = """
    public static void writeOwnerToNBT(ValueOutput output, NameUUIDPair owner) {
        if (owner != null) {
            output.putLong("OwnerMSB", owner.uuid.getMostSignificantBits());
            output.putLong("OwnerLSB", owner.uuid.getLeastSignificantBits());
            output.putString("OwnerName", owner.name);
        }
    }

    public static NameUUIDPair readOwnerFromNBT(ValueInput input) {
        long msb = input.getLongOr("OwnerMSB", 0L);
        long lsb = input.getLongOr("OwnerLSB", 0L);
        String str = input.getStringOr("OwnerName", "");
        return new NameUUIDPair(str, new UUID(msb, lsb));
    }

"""
        text = text.rsplit("}", 1)[0] + insert + "}\n"
    # Registry#get(id) returns a holder Optional; the value lookup is explicit.
    text = text.replace(
        "net.minecraft.core.registries.BuiltInRegistries.ITEM.get(itemId)",
        "net.minecraft.core.registries.BuiltInRegistries.ITEM.getValue(itemId)"
    )
    util.write_text(text, encoding="utf-8")


# Peripheral base persistence.
peripheral = DST / "src/main/java/net/montoyo/wd/entity/AbstractPeripheralBlockEntity.java"
if peripheral.exists():
    text = peripheral.read_text(encoding="utf-8")
    text = text.replace("import net.minecraft.nbt.CompoundTag;\n", "")
    text = text.replace("import net.minecraft.core.HolderLookup;\n", "")
    if "import net.minecraft.world.level.storage.ValueInput;" not in text:
        text = text.replace(
            "import net.minecraft.world.level.chunk.LevelChunk;",
            "import net.minecraft.world.level.chunk.LevelChunk;\nimport net.minecraft.world.level.storage.ValueInput;\nimport net.minecraft.world.level.storage.ValueOutput;"
        )
    old_start = text.find("    // TODO\n    @Override\n    public void loadAdditional(")
    old_end = text.find("    // serializeNBT/deserializeNBT", old_start)
    if old_start >= 0 and old_end >= 0:
        replacement = """    @Override
    protected void loadAdditional(ValueInput input) {
        super.loadAdditional(input);
        var child = input.child("WDScreen");
        if (child.isPresent()) {
            ValueInput scr = child.get();
            screenPos = new Vector3i(
                    scr.getIntOr("X", 0),
                    scr.getIntOr("Y", 0),
                    scr.getIntOr("Z", 0));
            int ordinal = scr.getByteOr("Side", (byte) 0);
            screenSide = BlockSide.values()[Math.max(0, Math.min(BlockSide.values().length - 1, ordinal))];
        } else {
            screenPos = null;
            screenSide = null;
        }
    }

    @Override
    protected void saveAdditional(ValueOutput output) {
        super.saveAdditional(output);
        if (screenPos != null && screenSide != null) {
            ValueOutput scr = output.child("WDScreen");
            scr.putInt("X", screenPos.x);
            scr.putInt("Y", screenPos.y);
            scr.putInt("Z", screenPos.z);
            scr.putByte("Side", (byte) screenSide.ordinal());
        }
    }

"""
        text = text[:old_start] + replacement + text[old_end:]
    peripheral.write_text(text, encoding="utf-8")


# Child block entities now override ValueInput/ValueOutput too.
for rel in [
    "src/main/java/net/montoyo/wd/entity/ServerBlockEntity.java",
    "src/main/java/net/montoyo/wd/entity/AbstractInterfaceBlockEntity.java",
]:
    p = DST / rel
    if p.exists():
        text = p.read_text(encoding="utf-8")
        text = text.replace("import net.minecraft.nbt.CompoundTag;\n", "")
        text = text.replace("import net.minecraft.core.HolderLookup;\n", "")
        if "import net.minecraft.world.level.storage.ValueInput;" not in text:
            first_import = text.find("import ")
            text = text[:first_import] + "import net.minecraft.world.level.storage.ValueInput;\nimport net.minecraft.world.level.storage.ValueOutput;\n" + text[first_import:]
        text = re.sub(
            r'@Override\s+public void loadAdditional\(CompoundTag tag,\s*net\.minecraft\.core\.HolderLookup\.Provider provider\)\s*\{\s*super\.loadAdditional\(tag, provider\);\s*owner = Util\.readOwnerFromNBT\(tag\);\s*\}',
            '@Override\\n    protected void loadAdditional(ValueInput input) {\\n        super.loadAdditional(input);\\n        owner = Util.readOwnerFromNBT(input);\\n    }',
            text, flags=re.S
        )
        text = re.sub(
            r'@Override\s+protected void saveAdditional\(CompoundTag tag,\s*HolderLookup\.Provider provider\)\s*\{\s*super\.saveAdditional\(tag, provider\);\s*Util\.writeOwnerToNBT\(tag, owner\);\s*\}',
            '@Override\\n    protected void saveAdditional(ValueOutput output) {\\n        super.saveAdditional(output);\\n        Util.writeOwnerToNBT(output, owner);\\n    }',
            text, flags=re.S
        )
        p.write_text(text, encoding="utf-8")


redstone = DST / "src/main/java/net/montoyo/wd/entity/RedstoneControlBlockEntity.java"
if redstone.exists():
    text = redstone.read_text(encoding="utf-8")
    text = text.replace("import net.minecraft.nbt.CompoundTag;\n", "")
    text = text.replace("import net.minecraft.core.HolderLookup;\n", "")
    if "import net.minecraft.world.level.storage.ValueInput;" not in text:
        text = text.replace(
            "import net.minecraft.world.level.block.state.BlockState;",
            "import net.minecraft.world.level.block.state.BlockState;\nimport net.minecraft.world.level.storage.ValueInput;\nimport net.minecraft.world.level.storage.ValueOutput;"
        )
    text = re.sub(
        r'@Override\s+public void loadAdditional\(CompoundTag tag,\s*net\.minecraft\.core\.HolderLookup\.Provider provider\)\s*\{.*?\n\s*\}',
        '''@Override
    protected void loadAdditional(ValueInput input) {
        super.loadAdditional(input);
        risingEdgeURL = input.getStringOr("RisingEdgeURL", "");
        fallingEdgeURL = input.getStringOr("FallingEdgeURL", "");
        state = input.getBooleanOr("Powered", false);
    }''',
        text, count=1, flags=re.S
    )
    text = re.sub(
        r'@Override\s+protected void saveAdditional\(CompoundTag tag,\s*HolderLookup\.Provider provider\)\s*\{.*?\n\s*\}',
        '''@Override
    protected void saveAdditional(ValueOutput output) {
        super.saveAdditional(output);
        output.putString("RisingEdgeURL", risingEdgeURL);
        output.putString("FallingEdgeURL", fallingEdgeURL);
        output.putBoolean("Powered", state);
    }''',
        text, count=1, flags=re.S
    )
    text = text.replace(".dimension().location()", ".dimension().identifier()")
    redstone.write_text(text, encoding="utf-8")


# ItemMinePad's use contract returns InteractionResult in 26.2.
minepad = DST / "src/main/java/net/montoyo/wd/item/ItemMinePad2.java"
if minepad.exists():
    text = minepad.read_text(encoding="utf-8")
    text = text.replace("import net.minecraft.world.InteractionResultHolder;\n", "")
    text = re.sub(r"public InteractionResultHolder<ItemStack> use\(", "public InteractionResult use(", text)
    text = re.sub(r"InteractionResultHolder\.success\([^)]*\)", "InteractionResult.SUCCESS", text)
    text = re.sub(r"InteractionResultHolder\.pass\([^)]*\)", "InteractionResult.PASS", text)
    minepad.write_text(text, encoding="utf-8")


# ClientProxy final 26.2 compatibility.
client_proxy = DST / "src/main/java/net/montoyo/wd/client/ClientProxy.java"
if client_proxy.exists():
    text = client_proxy.read_text(encoding="utf-8")
    text = text.replace("import net.minecraft.client.gui.GuiGraphics;", "import net.minecraft.client.gui.GuiGraphicsExtractor;")
    text = re.sub(r"\bGuiGraphics\b", "GuiGraphicsExtractor", text)
    text = text.replace("camera.getEntity()", "camera.entity()")
    text = text.replace("Screen.hasShiftDown()", "Minecraft.getInstance().hasShiftDown()")
    text = text.replace("Minecraft.getInstance().getWindow().getWindow()", "Minecraft.getInstance().getWindow()")
    text = text.replace("ep.getInventory().items", "ep.getInventory().getNonEquipmentItems()")
    # Offhand is slot 40 in 26.2; keep the same one-entry update semantics.
    text = text.replace(
        "updateInventory(ep.getInventory().offhand, ep.getItemInHand(InteractionHand.OFF_HAND), 1);",
        "updateInventory(net.minecraft.core.NonNullList.of(ItemStack.EMPTY, ep.getInventory().getItem(40)), ep.getItemInHand(InteractionHand.OFF_HAND), 1);"
    )
    text = text.replace(".dimension().location()", ".dimension().identifier()")
    text = text.replace("tag.getString(\"PadURL\")", "tag.getStringOr(\"PadURL\", \"\")")
    text = text.replace("new KeyMapping(\"webdisplays.key.toggle_mouse\", GLFW.GLFW_KEY_R, \"key.categories.misc\")",
                        "new KeyMapping(\"webdisplays.key.toggle_mouse\", GLFW.GLFW_KEY_R, KeyMapping.Category.MISC)")
    # UUID is stored by CustomData; CompoundTag no longer has getUUID helper.
    text = text.replace(
        'tag.getUUID("PadID")',
        'tag.read("PadID", net.minecraft.core.UUIDUtil.CODEC).orElse(new java.util.UUID(0L, 0L))'
    )
    # Old crosshair callback used raw immediate GL GUI drawing. Keep the feature
    # staged out until its 26.2 HUD extraction hook is registered, rather than
    # issuing invalid RenderSystem state calls.
    text = remove_java_method(text, "public static void renderCrosshair(")
    client_proxy.write_text(text, encoding="utf-8")


# Mouse mixin current screen accessor.
mouse_mixin = DST / "src/main/java/net/montoyo/wd/mixins/MouseHandlerMixin.java"
if mouse_mixin.exists():
    text = mouse_mixin.read_text(encoding="utf-8")
    text = text.replace("Minecraft.getInstance().screen", "Minecraft.getInstance().gui.screen()")
    mouse_mixin.write_text(text, encoding="utf-8")


# Main mod loader state and GameProfile record access.
webdisplays_java = DST / "src/main/java/net/montoyo/wd/WebDisplays.java"
if webdisplays_java.exists():
    text = webdisplays_java.read_text(encoding="utf-8")
    text = text.replace("FMLEnvironment.dist", "net.neoforged.fml.loading.FMLLoader.getCurrent().getDist()")
    text = text.replace("FMLEnvironment.production", "net.neoforged.fml.loading.FMLLoader.getCurrent().isProduction()")
    text = text.replace(".getGameProfile().getId()", ".getGameProfile().id()")
    webdisplays_java.write_text(text, encoding="utf-8")


# Direction import lost by the older source migration.
keyboard_right = DST / "src/main/java/net/montoyo/wd/block/KeyboardBlockRight.java"
if keyboard_right.exists():
    text = keyboard_right.read_text(encoding="utf-8")
    if "import net.minecraft.core.Direction;" not in text:
        text = text.replace("import net.minecraft.core.BlockPos;", "import net.minecraft.core.BlockPos;\nimport net.minecraft.core.Direction;")
    keyboard_right.write_text(text, encoding="utf-8")


# 26.2 GUI input bridge. Existing WebDisplays screens can retain their legacy
# overloads; Minecraft calls these event-object overrides.
wdscreen = DST / "src/main/java/net/montoyo/wd/client/gui/WDScreen.java"
if wdscreen.exists():
    text = wdscreen.read_text(encoding="utf-8")
    text = text.replace("import net.minecraft.client.gui.GuiGraphics;", "import net.minecraft.client.gui.GuiGraphicsExtractor;")
    text = re.sub(r"\bGuiGraphics\b", "GuiGraphicsExtractor", text)
    for imp in [
        "import net.minecraft.client.input.KeyEvent;",
        "import net.minecraft.client.input.MouseButtonEvent;",
        "import net.minecraft.client.input.CharacterEvent;"
    ]:
        if imp not in text:
            text = text.replace("import net.minecraft.client.Minecraft;", "import net.minecraft.client.Minecraft;\n" + imp)
    # Render entry point.
    text = text.replace(
        "public void render(GuiGraphicsExtractor poseStack, int mouseX, int mouseY, float ptt)",
        "public void extractRenderState(GuiGraphicsExtractor poseStack, int mouseX, int mouseY, float ptt)"
    )
    text = text.replace("renderBackground(poseStack, mouseX, mouseY, ptt);", "")
    text = text.replace("RenderSystem.setShaderColor(1.f, 1.f, 1.f, 1.f);", "")
    # Tooltips.
    text = text.replace("poseStack.renderTooltip(Minecraft.getInstance().font, is, x, y);",
                        "poseStack.setTooltipForNextFrame(Minecraft.getInstance().font, is, x, y);")
    text = text.replace("poseStack.renderTooltip(Minecraft.getInstance().font, lines.stream().map(a -> FormattedCharSequence.forward(a, Style.EMPTY)).collect(Collectors.toList()), x, y);",
                        "poseStack.setTooltipForNextFrame(Minecraft.getInstance().font, lines.stream().map(a -> FormattedCharSequence.forward(a, Style.EMPTY)).collect(Collectors.toList()), x, y);")
    # Add modern event methods before isPauseScreen if not already present.
    if "mouseClicked(MouseButtonEvent event" not in text:
        bridge = """
    @Override
    public boolean mouseClicked(MouseButtonEvent event, boolean doubleClick) {
        return mouseClicked(event.x(), event.y(), event.button());
    }

    @Override
    public boolean mouseReleased(MouseButtonEvent event) {
        return mouseReleased(event.x(), event.y(), event.button());
    }

    @Override
    public boolean mouseDragged(MouseButtonEvent event, double dragX, double dragY) {
        return mouseDragged(event.x(), event.y(), event.button(), dragX, dragY);
    }

    @Override
    public boolean keyPressed(KeyEvent event) {
        return keyPressed(event.key(), event.scancode(), event.modifiers());
    }

    @Override
    public boolean keyReleased(KeyEvent event) {
        return keyReleased(event.key(), event.scancode(), event.modifiers());
    }

    @Override
    public boolean charTyped(CharacterEvent event) {
        return charTyped((char) event.codepoint(), 0);
    }

"""
        text = text.replace("    @Override\n    public boolean isPauseScreen()", bridge + "    @Override\n    public boolean isPauseScreen()")
    wdscreen.write_text(text, encoding="utf-8")


# Final GUI naming migration after all screen/control source copies.
for java in (DST / "src/main/java/net/montoyo/wd/client/gui").rglob("*.java"):
    text = java.read_text(encoding="utf-8")
    text = text.replace("import net.minecraft.client.gui.GuiGraphics;", "import net.minecraft.client.gui.GuiGraphicsExtractor;")
    text = re.sub(r"\bGuiGraphics\b", "GuiGraphicsExtractor", text)
    text = re.sub(r"\bpublic void render\(GuiGraphicsExtractor ", "public void extractRenderState(GuiGraphicsExtractor ", text)
    text = text.replace("super.render(graphics,", "super.extractRenderState(graphics,")
    text = text.replace("super.render(poseStack,", "super.extractRenderState(poseStack,")
    text = text.replace(".drawString(", ".text(")
    text = text.replace(".renderItemDecorations(", ".itemDecorations(")
    text = text.replace(".renderItem(", ".item(")
    text = text.replace(".renderTooltip(", ".setTooltipForNextFrame(")
    java.write_text(text, encoding="utf-8")


# Remove obsolete immediate-mode helper dependencies from the base Control.
control = DST / "src/main/java/net/montoyo/wd/client/gui/controls/Control.java"
if control.exists():
    text = control.read_text(encoding="utf-8")
    text = text.replace("import com.mojang.blaze3d.platform.GlStateManager;", "import com.mojang.blaze3d.opengl.GlStateManager;")
    text = text.replace("import net.minecraft.client.renderer.RenderType;", "import net.minecraft.client.renderer.rendertype.RenderType;")
    # The old FBO helper is not used by 26.2 screen extraction; leave a simple
    # coordinate-compatible no-op signature until List is migrated below.
    text = re.sub(
        r'public void fillRect\(MultiBufferSource\.BufferSource source, int x, double y, int w, int h, int color\) \{.*?\n    \}',
        'public void fillRect(Object source, int x, double y, int w, int h, int color) { }',
        text, count=1, flags=re.S
    )
    control.write_text(text, encoding="utf-8")


# Misc current API normalization that remains safe after generated files exist.
for java in java_root.rglob("*.java"):
    text = java.read_text(encoding="utf-8")
    text = text.replace(".getGameProfile().getId()", ".getGameProfile().id()")
    text = text.replace(".getGameProfile().getName()", ".getGameProfile().name()")
    text = text.replace(".dimension().location()", ".dimension().identifier()")
    text = text.replace("Screen.hasControlDown()", "Minecraft.getInstance().hasControlDown()")
    text = text.replace("Screen.hasShiftDown()", "Minecraft.getInstance().hasShiftDown()")
    java.write_text(text, encoding="utf-8")

print("Final 26.2 normalization complete")


# ===========================================================================
# CORE SEMANTIC FIXES AFTER FINAL NORMALIZATION
# ===========================================================================

def replace_method_by_signature(source: str, signature: str, replacement: str) -> str:
    sig = source.find(signature)
    if sig < 0:
        return source
    # Start at annotation if immediately above.
    line_start = source.rfind("\n", 0, sig) + 1
    pre_start = source.rfind("\n", 0, max(0, line_start - 1)) + 1
    if "@Override" in source[pre_start:line_start]:
        line_start = pre_start
    brace = source.find("{", sig)
    if brace < 0:
        return source
    depth = 0
    i = brace
    while i < len(source):
        if source[i] == "{":
            depth += 1
        elif source[i] == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                while end < len(source) and source[end] in " \t\r\n":
                    end += 1
                return source[:line_start] + replacement.rstrip() + "\n\n" + source[end:]
        i += 1
    raise RuntimeError("Unbalanced method: " + signature)


# Force block-entity persistence methods to ValueInput/ValueOutput regardless of
# which 1.21.x source variant was copied earlier.
for rel, owner in [
    ("src/main/java/net/montoyo/wd/entity/ServerBlockEntity.java", True),
    ("src/main/java/net/montoyo/wd/entity/AbstractInterfaceBlockEntity.java", True),
]:
    p = DST / rel
    if p.exists():
        text = p.read_text(encoding="utf-8")
        text = text.replace("import net.minecraft.nbt.CompoundTag;\n", "")
        text = text.replace("import net.minecraft.core.HolderLookup;\n", "")
        if "import net.minecraft.world.level.storage.ValueInput;" not in text:
            pkg_end = text.find("\n", text.find("package "))
            text = text[:pkg_end+1] + "\nimport net.minecraft.world.level.storage.ValueInput;\nimport net.minecraft.world.level.storage.ValueOutput;\n" + text[pkg_end+1:]
        text = replace_method_by_signature(
            text, "loadAdditional(",
            """    @Override
    protected void loadAdditional(ValueInput input) {
        super.loadAdditional(input);
        owner = Util.readOwnerFromNBT(input);
    }"""
        )
        text = replace_method_by_signature(
            text, "saveAdditional(",
            """    @Override
    protected void saveAdditional(ValueOutput output) {
        super.saveAdditional(output);
        Util.writeOwnerToNBT(output, owner);
    }"""
        )
        p.write_text(text, encoding="utf-8")


redstone = DST / "src/main/java/net/montoyo/wd/entity/RedstoneControlBlockEntity.java"
if redstone.exists():
    text = redstone.read_text(encoding="utf-8")
    text = text.replace("import net.minecraft.nbt.CompoundTag;\n", "")
    text = text.replace("import net.minecraft.core.HolderLookup;\n", "")
    if "import net.minecraft.world.level.storage.ValueInput;" not in text:
        pkg_end = text.find("\n", text.find("package "))
        text = text[:pkg_end+1] + "\nimport net.minecraft.world.level.storage.ValueInput;\nimport net.minecraft.world.level.storage.ValueOutput;\n" + text[pkg_end+1:]
    text = replace_method_by_signature(
        text, "loadAdditional(",
        """    @Override
    protected void loadAdditional(ValueInput input) {
        super.loadAdditional(input);
        risingEdgeURL = input.getStringOr("RisingEdgeURL", "");
        fallingEdgeURL = input.getStringOr("FallingEdgeURL", "");
        state = input.getBooleanOr("Powered", false);
    }"""
    )
    text = replace_method_by_signature(
        text, "saveAdditional(",
        """    @Override
    protected void saveAdditional(ValueOutput output) {
        super.saveAdditional(output);
        output.putString("RisingEdgeURL", risingEdgeURL);
        output.putString("FallingEdgeURL", fallingEdgeURL);
        output.putBoolean("Powered", state);
    }"""
    )
    redstone.write_text(text, encoding="utf-8")


# Legacy overloads remain deliberately for WebDisplays' own controls, but only
# event-object methods override Minecraft 26.2 interfaces.
wdscreen = DST / "src/main/java/net/montoyo/wd/client/gui/WDScreen.java"
if wdscreen.exists():
    text = wdscreen.read_text(encoding="utf-8")
    for signature in [
        "public boolean charTyped(char codePoint, int modifiers)",
        "public boolean mouseClicked(double mouseX, double mouseY, int button)",
        "public boolean mouseReleased(double mouseX, double mouseY, int button)",
        "public boolean mouseDragged(double mouseX, double mouseY, int button, double dragX, double dragY)",
        "public boolean keyPressed(int keyCode, int scanCode, int modifiers)",
        "public boolean keyReleased(int keyCode, int scanCode, int modifiers)",
    ]:
        text = text.replace("    @Override\n    " + signature, "    " + signature)
    wdscreen.write_text(text, encoding="utf-8")


# CompoundTag scalar accessors return Optional in 26.2. Apply only to ordinary
# client/custom-data code, not ValueInput code.
for java in java_root.rglob("*.java"):
    text = java.read_text(encoding="utf-8")
    if "ValueInput input" not in text or "CompoundTag" in text:
        text = re.sub(r'(?<!getStringOr\()\.getString\("([^"]+)"\)', r'.getStringOr("\1", "")', text)
        text = re.sub(r'(?<!getIntOr\()\.getInt\("([^"]+)"\)', r'.getIntOr("\1", 0)', text)
        text = re.sub(r'(?<!getLongOr\()\.getLong\("([^"]+)"\)', r'.getLongOr("\1", 0L)', text)
        text = re.sub(r'(?<!getDoubleOr\()\.getDouble\("([^"]+)"\)', r'.getDoubleOr("\1", 0.0)', text)
        text = re.sub(r'(?<!getBooleanOr\()\.getBoolean\("([^"]+)"\)', r'.getBooleanOr("\1", false)', text)
        text = re.sub(r'(?<!getByteOr\()\.getByte\("([^"]+)"\)', r'.getByteOr("\1", (byte)0)', text)
    java.write_text(text, encoding="utf-8")


# MinePad custom data uses codecs for UUIDs in 26.2.
minepad = DST / "src/main/java/net/montoyo/wd/item/ItemMinePad2.java"
if minepad.exists():
    text = minepad.read_text(encoding="utf-8")
    text = text.replace("import net.minecraft.world.InteractionResultHolder;\n", "")
    if "import net.minecraft.core.UUIDUtil;" not in text:
        text = text.replace("import net.minecraft.nbt.CompoundTag;", "import net.minecraft.nbt.CompoundTag;\nimport net.minecraft.core.UUIDUtil;")
    text = re.sub(r"public InteractionResultHolder<ItemStack> use\(", "public InteractionResult use(", text)
    text = re.sub(
        r"return new InteractionResultHolder<>\(ok \? InteractionResult\.SUCCESS : InteractionResult\.PASS, is\);",
        "return ok ? InteractionResult.SUCCESS : InteractionResult.PASS;",
        text
    )
    text = text.replace(
        'copyTag().getUUID("PadID")',
        'copyTag().read("PadID", UUIDUtil.CODEC).orElse(new UUID(0L, 0L))'
    )
    text = text.replace(
        'tag.putUUID("PadID", uuid)',
        'tag.store("PadID", UUIDUtil.CODEC, uuid)'
    )
    # Current hover-text API uses a Consumer and TooltipDisplay.
    text = re.sub(
        r'@Override\s+public void appendHoverText\(ItemStack stack,\s*TooltipContext context,\s*List<Component> tooltip,\s*TooltipFlag flag\)\s*\{\s*super\.appendHoverText\(stack, context, tooltip, flag\);',
        '''@Override
    public void appendHoverText(ItemStack stack, TooltipContext context,
                                net.minecraft.world.item.component.TooltipDisplay display,
                                java.util.function.Consumer<Component> tooltip,
                                TooltipFlag flag) {
        super.appendHoverText(stack, context, display, tooltip, flag);''',
        text, flags=re.S
    )
    minepad.write_text(text, encoding="utf-8")


# Ownership thief custom tag scalars.
thief = DST / "src/main/java/net/montoyo/wd/item/ItemOwnershipThief.java"
if thief.exists():
    text = thief.read_text(encoding="utf-8")
    text = re.sub(r'tag\.getInt\("([^"]+)"\)', r'tag.getIntOr("\1", 0)', text)
    text = re.sub(r'tag\.getByte\("([^"]+)"\)', r'tag.getByteOr("\1", (byte)0)', text)
    thief.write_text(text, encoding="utf-8")


# SoundInstance renamed its resource accessor.
audio = DST / "src/main/java/net/montoyo/wd/client/audio/WDAudioSource.java"
if audio.exists():
    text = audio.read_text(encoding="utf-8")
    text = text.replace("public Identifier getLocation()", "public Identifier getIdentifier()")
    text = text.replace("public ResourceLocation getLocation()", "public Identifier getIdentifier()")
    audio.write_text(text, encoding="utf-8")


# Remove imports whose old types were replaced by extractor/state APIs.
control = DST / "src/main/java/net/montoyo/wd/client/gui/controls/Control.java"
if control.exists():
    text = control.read_text(encoding="utf-8")
    text = text.replace("import net.minecraft.client.renderer.MultiBufferSource;\n", "")
    control.write_text(text, encoding="utf-8")


print("Core semantic fixes complete")


# ===========================================================================
# GUI / REGISTRY 26.2 PORT
# ===========================================================================

controls = DST / "src/main/java/net/montoyo/wd/client/gui/controls"

# Base control: preserve WebDisplays' immediate-mode helper API at the call-site,
# but implement it with the 26.2 GUI extractor.
(controls / "Control.java").write_text("""package net.montoyo.wd.client.gui.controls;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.resources.language.I18n;
import net.minecraft.resources.Identifier;
import net.montoyo.wd.client.gui.WDScreen;
import net.montoyo.wd.client.gui.loading.JsonOWrapper;
import net.montoyo.wd.utilities.data.Bounds;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.api.distmarker.OnlyIn;

@OnlyIn(Dist.CLIENT)
public abstract class Control {
    public static final int COLOR_BLACK    = 0xFF000000;
    public static final int COLOR_WHITE    = 0xFFFFFFFF;
    public static final int COLOR_RED      = 0xFFFF0000;
    public static final int COLOR_GREEN    = 0xFF00FF00;
    public static final int COLOR_BLUE     = 0xFF0000FF;
    public static final int COLOR_CYAN     = 0xFF00FFFF;
    public static final int COLOR_MANGENTA = 0xFFFF00FF;
    public static final int COLOR_YELLOW   = 0xFFFFFF00;

    protected final Minecraft mc;
    protected final Font font;
    protected static WDScreen parent;
    protected String name;
    protected Object userdata;
    private Identifier boundTexture;

    public Control() {
        mc = Minecraft.getInstance();
        font = mc.font;
        parent = WDScreen.CURRENT_SCREEN;
    }

    public Object getUserdata() { return userdata; }
    public void setUserdata(Object userdata) { this.userdata = userdata; }
    public boolean keyTyped(int keyCode, int modifier) { return false; }
    public boolean keyUp(int key, int scanCode, int modifiers) { return false; }
    public boolean keyDown(int key, int scanCode, int modifiers) { return false; }
    public boolean mouseClicked(double mouseX, double mouseY, int mouseButton) { return false; }
    public void unfocus() {}
    public boolean mouseReleased(double mouseX, double mouseY, int state) { return false; }
    public boolean mouseClickMove(double mouseX, double mouseY, int button, double dragX, double dragY) { return false; }
    public boolean mouseMove(double mouseX, double mouseY) { return false; }
    public boolean mouseScroll(double mouseX, double mouseY, double amount) { return false; }
    public void draw(GuiGraphicsExtractor graphics, int mouseX, int mouseY, float partialTick) {}
    public void postDraw(GuiGraphicsExtractor graphics, int mouseX, int mouseY, float partialTick) {}
    public void destroy() {}
    public WDScreen getParent() { return parent; }

    public abstract int getX();
    public abstract int getY();
    public abstract int getWidth();
    public abstract int getHeight();
    public abstract void setPos(int x, int y);

    public void fillRect(GuiGraphicsExtractor graphics, int x, double y, int w, int h, int color) {
        graphics.fill(x, (int)y, x + w, (int)y + h, color);
    }

    public void fillTexturedRect(GuiGraphicsExtractor graphics, int x, int y, int w, int h,
                                 double u1, double v1, double u2, double v2) {
        if (boundTexture != null) {
            graphics.blit(boundTexture, x, y, x + w, y + h,
                    (float)u1, (float)u2, (float)v1, (float)v2);
        }
    }

    public static void blend(boolean enable) {
        // GUI render pipelines own blend state in 26.2.
    }

    public void bindTexture(Identifier texture) {
        this.boundTexture = texture;
    }

    public void drawBorder(GuiGraphicsExtractor graphics, int x, int y, int w, int h, int color) {
        drawBorder(graphics, x, y, w, h, color, 1.0);
    }

    public void drawBorder(GuiGraphicsExtractor graphics, int x, int y, int w, int h, int color, double size) {
        int s = Math.max(1, (int)Math.ceil(size));
        graphics.fill(x, y, x + w, y + s, color);
        graphics.fill(x, y + h - s, x + w, y + h, color);
        graphics.fill(x, y, x + s, y + h, color);
        graphics.fill(x + w - s, y, x + w, y + h, color);
    }

    public static String tr(String text) {
        if(text.length() >= 2 && text.charAt(0) == '$') {
            return text.charAt(1) == '$' ? text.substring(1) : I18n.get(text.substring(1));
        }
        return text;
    }

    public void setName(String name) { this.name = name; }
    public String getName() { return name; }
    public void load(JsonOWrapper json) { name = json.getString("name", ""); }

    public static Bounds findBounds(java.util.List<Control> controlList) {
        int minX = Integer.MAX_VALUE, minY = Integer.MAX_VALUE;
        int maxX = Integer.MIN_VALUE, maxY = Integer.MIN_VALUE;
        for(Control ctrl : controlList) {
            int x = ctrl.getX(), y = ctrl.getY();
            minX = Math.min(minX, x);
            minY = Math.min(minY, y);
            maxX = Math.max(maxX, x + ctrl.getWidth());
            maxY = Math.max(maxY, y + ctrl.getHeight());
        }
        return new Bounds(minX, minY, maxX, maxY);
    }
}
""", encoding="utf-8")


# Direct extractor-based list; scissor replaces the legacy FBO.
(controls / "List.java").write_text("""package net.montoyo.wd.client.gui.controls;

import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.montoyo.wd.client.gui.loading.JsonOWrapper;
import java.util.ArrayList;

public class List extends BasicControl {
    private static class Entry {
        final String text;
        final Object userdata;
        Entry(String text, Object userdata) { this.text = text; this.userdata = userdata; }
    }

    public static class EntryClick extends Event<List> {
        private final int id;
        private final Entry entry;
        public EntryClick(List list) {
            source = list;
            id = list.selected;
            entry = list.content.get(list.selected);
        }
        public int getId() { return id; }
        public String getLabel() { return entry.text; }
        public Object getUserdata() { return entry.userdata; }
    }

    private int width, height;
    private final ArrayList<Entry> content = new ArrayList<>();
    private int selected = -1;
    private int selColor = 0xFF0080FF;
    private int contentH;
    private int scrollSize;
    private double scrollPos;
    private boolean scrolling;
    private double scrollGrab;

    public List() { content.add(new Entry("", null)); selected = 0; }
    public List(int x, int y, int w, int h) {
        this.x=x; this.y=y; width=w; height=h; scrollSize=Math.max(1,h-2);
    }

    private int getYOffset() {
        int travel = height - 2 - scrollSize;
        int overflow = contentH - height;
        if (travel <= 0 || overflow <= 0) return 0;
        return (int)(scrollPos / travel * overflow);
    }

    private boolean isInScrollbar(double mx,double my) {
        return mx>=x+width-5 && mx<=x+width-1 && my>=y+1+scrollPos && my<=y+1+scrollPos+scrollSize;
    }

    @Override public void destroy() {}
    public void setSize(int w,int h){width=w;height=h;updateContent();}
    public void setWidth(int w){width=w;updateContent();}
    public void setHeight(int h){height=h;updateContent();}
    @Override public int getWidth(){return width;}
    @Override public int getHeight(){return height;}

    public void updateContent() {
        contentH = content.size()*12+4;
        int h2=Math.max(1,height-2);
        if(contentH<=h2){scrollSize=h2;scrollPos=0;}
        else scrollSize=Math.max(4,h2*h2/contentH);
    }

    public int addElement(String s){return addElement(s,null);}
    public int addElement(String s,Object u){content.add(new Entry(s,u));updateContent();return content.size()-1;}
    public int addElementRaw(String s){return addElementRaw(s,null);}
    public int addElementRaw(String s,Object u){content.add(new Entry(s,u));return content.size()-1;}

    @Override public void setDisabled(boolean d){disabled=d;if(d)selected=-1;}
    @Override public void disable(){disabled=true;selected=-1;}

    @Override public boolean mouseMove(double mx,double my){
        int sel=-1;
        if(!disabled && mx>=x+1 && mx<=x+width-6 && my>=y+2 && my<=y+height-2){
            sel=(int)((my-(y+4-getYOffset()))/12);
            if(sel<0||sel>=content.size())sel=-1;
        }
        if(selected!=sel){selected=sel;return true;}
        return false;
    }

    @Override public boolean mouseClicked(double mx,double my,int b){
        if(disabled||b!=0)return false;
        if(isInScrollbar(mx,my)){scrolling=true;scrollGrab=my-(y+1+scrollPos);return true;}
        if(selected>=0){parent.actionPerformed(new EntryClick(this));return true;}
        return false;
    }
    @Override public boolean mouseReleased(double mx,double my,int b){if(!disabled&&scrolling){scrolling=false;return true;}return false;}
    @Override public boolean mouseScroll(double mx,double my,double amount){
        if(disabled||scrolling||mx<x||mx>x+width||my<y||my>y+height)return false;
        int travel=height-2-scrollSize;
        int overflow=contentH-height;
        if(travel<=0||overflow<=0)return false;
        double disp=12.0*travel/overflow;
        scrollPos=Math.max(0,Math.min(travel,scrollPos+(amount<0?disp:-disp)));
        return true;
    }
    @Override public boolean mouseClickMove(double mx,double my,int button,double dx,double dy){
        if(disabled||!scrolling)return false;
        int travel=height-2-scrollSize;
        scrollPos=Math.max(0,Math.min(travel,my-scrollGrab-y-1));
        return true;
    }

    @Override public void draw(GuiGraphicsExtractor g,int mouseX,int mouseY,float partialTick){
        if(!visible)return;
        g.fill(x,y,x+width,y+height,COLOR_BLACK);
        g.enableScissor(x+1,y+1,x+width-6,y+height-1);
        int offset=y+4-getYOffset();
        for(int i=0;i<content.size();i++){
            int py=i*12+offset;
            if(py+12<y+1)continue;
            if(py>=y+height-1)break;
            int color=(i==selected)?selColor:COLOR_WHITE;
            g.text(font,content.get(i).text,x+4,py,color);
        }
        g.disableScissor();
        drawBorder(g,x,y,width,height,0xFF808080);
        g.fill(x+width-5,(int)(y+1+scrollPos),x+width-1,(int)(y+1+scrollPos+scrollSize),
                (scrolling||isInScrollbar(mouseX,mouseY))?0xFF202020:0xFF404040);
    }

    public String getEntryLabel(int id){return content.get(id).text;}
    public Object getEntryUserdata(int id){return content.get(id).userdata;}
    public int findEntryByLabel(String l){for(int i=0;i<content.size();i++)if(content.get(i).text.equals(l))return i;return -1;}
    public int findEntryByUserdata(Object o){for(int i=0;i<content.size();i++)if(java.util.Objects.equals(content.get(i).userdata,o))return i;return -1;}
    public void setSelectionColor(int c){selColor=c;}
    public int getSelectionColor(){return selColor;}
    public int getElementCount(){return content.size();}
    public void removeElement(int id){if(selected!=-1&&id==content.size()-1)selected=-1;content.remove(id);updateContent();}
    public void removeElementRaw(int id){if(selected!=-1&&id==content.size()-1)selected=-1;content.remove(id);}
    public void clear(){content.clear();scrollPos=0;scrolling=false;scrollSize=Math.max(1,height-2);selected=-1;}
    public void clearRaw(){content.clear();scrollPos=0;scrolling=false;selected=-1;}
    @Override public void load(JsonOWrapper json){super.load(json);width=json.getInt("width",100);height=json.getInt("height",100);selColor=json.getColor("selectionColor",0xFF0080FF);updateContent();}
}
""", encoding="utf-8")


(controls / "UpgradeGroup.java").write_text("""package net.montoyo.wd.client.gui.controls;

import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.world.item.ItemStack;
import net.montoyo.wd.client.gui.loading.JsonOWrapper;
import java.util.ArrayList;

public class UpgradeGroup extends BasicControl {
    private int width;
    private int height;
    private ArrayList<ItemStack> upgrades;
    private ItemStack overStack;
    private ItemStack clickStack;

    public UpgradeGroup(){parent.requirePostDraw(this);}

    @Override public void draw(GuiGraphicsExtractor g,int mouseX,int mouseY,float partialTick){
        if(upgrades==null)return;
        int px=this.x;
        for(ItemStack stack:upgrades){
            if(stack==overStack&&!disabled) g.fill(px,y,px+16,y+16,0x80FF0000);
            g.item(stack,px,y);
            g.itemDecorations(font,stack,px,y);
            px+=18;
        }
    }
    @Override public void postDraw(GuiGraphicsExtractor g,int mouseX,int mouseY,float partialTick){
        if(overStack!=null) parent.drawItemStackTooltip(g,overStack,mouseX,mouseY);
    }
    @Override public int getWidth(){return width;}
    @Override public int getHeight(){return height;}
    public void setWidth(int w){width=w;}
    public void setHeight(int h){height=h;}
    public void setUpgrades(ArrayList<ItemStack> u){upgrades=u;}
    public ArrayList<ItemStack> getUpgrades(){return upgrades;}
    @Override public void load(JsonOWrapper json){super.load(json);width=json.getInt("width",0);height=json.getInt("height",16);}
    @Override public boolean mouseMove(double mx,double my){
        if(upgrades==null)return false;
        overStack=null;
        if(my>=y&&my<=y+16&&mx>=x){
            double rel=mx-x;int sel=(int)(rel/18);
            if(sel<upgrades.size()&&rel%18<=16)overStack=upgrades.get(sel);
            return true;
        }
        return false;
    }
    @Override public boolean mouseClicked(double mx,double my,int b){
        if(b==0&&mx>=x&&mx<=x+width&&my>=y&&my<=y+height){clickStack=overStack;return true;}
        return false;
    }
    @Override public boolean mouseReleased(double mx,double my,int b){
        if(b==0&&clickStack!=null){
            if(clickStack==overStack&&!disabled&&upgrades.contains(clickStack))parent.actionPerformed(new ClickEvent(this));
            clickStack=null;return true;
        }
        return false;
    }
    public ItemStack getMouseOverUpgrade(){return overStack;}
    public static class ClickEvent extends Event<UpgradeGroup>{
        private final ItemStack clickStack;
        public ClickEvent(UpgradeGroup src){source=src;clickStack=src.clickStack;}
        public ItemStack getMouseOverStack(){return clickStack;}
    }
}
""", encoding="utf-8")


# Recipe viewer, migrated to extractor item rendering. It remains functionally
# equivalent without old raw Lighting/ItemRenderer state.
recipe = DST / "src/main/java/net/montoyo/wd/client/gui/RenderRecipe.java"
if recipe.exists():
    text = recipe.read_text(encoding="utf-8")
    text = text.replace("import com.mojang.blaze3d.platform.Lighting;\n","")
    text = text.replace("import com.mojang.blaze3d.systems.RenderSystem;\n","")
    text = text.replace("import com.mojang.blaze3d.vertex.PoseStack;\n","")
    text = text.replace("import net.minecraft.client.renderer.entity.ItemRenderer;\n","")
    text = text.replace("private ItemRenderer renderItem;\n","")
    text = text.replace("renderItem = minecraft.getItemRenderer();\n","")
    text = text.replace("Lighting.setupForFlatItems();","")
    text = text.replace("Lighting.setupFor3DItems();","")
    text = text.replace("RenderSystem.setShaderColor(1.0f, 1.0f, 1.0f, 1.0f);","")
    text = text.replace("RenderSystem.setShaderTexture(0, CRAFTING_TABLE_GUI_TEXTURES);","")
    text = text.replace("renderBackground(context, mouseX, mouseY, partialTick);","extractBackground(context, mouseX, mouseY, partialTick);")
    text = text.replace("minecraft.setScreen(null)","minecraft.gui.setScreen(null)")
    recipe.write_text(text,encoding="utf-8")


# Make the shared MCEF native texture bridge reusable by MinePad GUI.
bridge = render_dir / "BrowserTextureBridge.java"
if bridge.exists():
    text = bridge.read_text(encoding="utf-8")
    text = text.replace("final class BrowserTextureBridge", "public final class BrowserTextureBridge")
    text = text.replace("static Identifier texture(", "public static Identifier texture(")
    bridge.write_text(text, encoding="utf-8")


# MinePad GUI: browser remains MCEF, but its frame is submitted through the
# normal 26.2 GUI texture path instead of raw GL/Tesselator calls.
minepad_gui = DST / "src/main/java/net/montoyo/wd/client/gui/GuiMinePad.java"
if minepad_gui.exists():
    text = minepad_gui.read_text(encoding="utf-8")
    for imp in [
        "import com.mojang.blaze3d.systems.RenderSystem;\n",
        "import com.mojang.blaze3d.vertex.BufferBuilder;\n",
        "import com.mojang.blaze3d.vertex.BufferUploader;\n",
        "import com.mojang.blaze3d.vertex.DefaultVertexFormat;\n",
        "import com.mojang.blaze3d.vertex.Tesselator;\n",
        "import com.mojang.blaze3d.vertex.VertexFormat;\n",
        "import net.minecraft.client.renderer.GameRenderer;\n"
    ]:
        text=text.replace(imp,"")
    if "import net.montoyo.wd.client.renderers.BrowserTextureBridge;" not in text:
        text=text.replace("import net.montoyo.wd.client.ClientProxy;","import net.montoyo.wd.client.ClientProxy;\nimport net.montoyo.wd.client.renderers.BrowserTextureBridge;\nimport net.minecraft.resources.Identifier;")
    text = remove_java_method(text, "private static void addRect(")
    render_sig = "public void extractRenderState(GuiGraphicsExtractor graphics, int mouseX, int mouseY, float ptt)"
    old_sig = "public void render(GuiGraphics graphics, int mouseX, int mouseY, float ptt)"
    if old_sig in text:
        text=text.replace(old_sig,render_sig)
    # Replace full render method with a clean extractor implementation.
    text = replace_method_by_signature(
        text, "public void extractRenderState(",
        """    @Override
    public void extractRenderState(GuiGraphicsExtractor graphics, int mouseX, int mouseY, float partialTick) {
        int savedWidth = width;
        int savedHeight = height;
        width = trueWidth;
        height = trueHeight;
        extractBackground(graphics, mouseX, mouseY, partialTick);
        width = savedWidth;
        height = savedHeight;

        int x0=(int)vx, y0=(int)vy, x1=(int)(vx+vw), y1=(int)(vy+vh);
        graphics.fill(x0, y0-16, x1, y0, 0xFFBABABA);
        graphics.fill(x0, y1, x1, y1+16, 0xFFBABABA);
        graphics.fill(x0-16, y0, x0, y1, 0xFFBABABA);
        graphics.fill(x1, y0, x1+16, y1, 0xFFBABABA);

        if (pad != null && pad.view instanceof MCEFBrowser browser && browser.getRenderer() != null) {
            Identifier texture = BrowserTextureBridge.texture(
                    browser, Math.max(1,(int)vw), Math.max(1,(int)vh));
            if (texture != null) graphics.blit(texture, x0, y0, x1, y1, 0f, 1f, 0f, 1f);
        }

        graphics.text(minecraft.font,
                Language.getInstance().getOrDefault("webdisplays.gui.minepad.close"),
                x0+4, y0-minecraft.font.lineHeight-3, 0xFFFFFFFF, true);
    }"""
    )
    text=text.replace("minecraft.getWindow().getWindow()","minecraft.getWindow().handle()")
    text=text.replace("Minecraft.getInstance().getWindow().getWindow()","Minecraft.getInstance().getWindow().handle()")
    text=text.replace("minecraft.setScreen(null)","minecraft.gui.setScreen(null)")
    text=text.replace("this.minecraft.popGuiLayer();","this.minecraft.gui.setScreen(null);")
    # Legacy modifier helpers moved to Minecraft instance.
    text=text.replace("hasControlDown()","minecraft.hasControlDown()")
    text=text.replace("hasAltDown()","false")
    text=text.replace("hasShiftDown()","minecraft.hasShiftDown()")
    minepad_gui.write_text(text,encoding="utf-8")


# BrotherBill's shader-era MinePad overlay depends on removed global matrix state.
# On 26.2 the MinePad GUI itself uses BrowserTextureBridge and normal GUI
# submission; keep this class as the queue API used by item code until the item
# special-renderer port consumes it.
overlay = render_dir / "MinePadOverlayRenderer.java"
if overlay.exists():
    overlay.write_text("""package net.montoyo.wd.client.renderers;

import com.mojang.blaze3d.vertex.PoseStack;

/**
 * Compatibility queue surface for the 26.2 MinePad special-renderer migration.
 * GUI MinePad rendering no longer uses raw global GL matrices.
 */
public final class MinePadOverlayRenderer {
    private MinePadOverlayRenderer() {}
    public static void queueRender(PoseStack poseStack, double x1, double y1, double x2, double y2, int textureId) {}
    public static void clearPendingRenders() {}
}
""", encoding="utf-8")


# 26.2 BlockEntityType has a public factory+Set constructor, no Builder.
tile = DST / "src/main/java/net/montoyo/wd/registry/TileRegistry.java"
if tile.exists():
    text = tile.read_text(encoding="utf-8")
    text = re.sub(
        r'BlockEntityType\.Builder\.of\(([^;]+?)\)\.build\(null\)',
        r'new BlockEntityType<>(\1)',
        text
    )
    # Convert factory,varargs blocks into factory, Set.of(blocks).
    text = re.sub(
        r'new BlockEntityType<>\(([^,\n]+),\s*([^)]+)\)',
        lambda m: 'new BlockEntityType<>(' + m.group(1) + ', java.util.Set.of(' + m.group(2) + '))',
        text
    )
    tile.write_text(text, encoding="utf-8")


# Avoid accidental global Optional rewrite of JDK Boolean system properties.
log = DST / "src/main/java/net/montoyo/wd/utilities/Log.java"
if log.exists():
    text=log.read_text(encoding="utf-8").replace("Boolean.getBooleanOr(", "Boolean.getBoolean(")
    # Previous mechanical replacement may have left a default argument.
    text=re.sub(r'Boolean\.getBoolean\(([^,]+),\s*false\)', r'Boolean.getBoolean(\1)', text)
    log.write_text(text,encoding="utf-8")


# Remove the stale crosshair mixin call while its 26.2 HUD render-state hook is
# being migrated; this prevents calling a deliberately removed legacy callback.
overlay_mixin = DST / "src/main/java/net/montoyo/wd/mixins/OverlayMixin.java"
if overlay_mixin.exists():
    text=overlay_mixin.read_text(encoding="utf-8")
    text=remove_java_method(text,"private void renderCrosshair(")
    text=remove_java_method(text,"public void renderCrosshair(")
    overlay_mixin.write_text(text,encoding="utf-8")


# Final call-site cleanup for extractor-based Control helpers.
for java in (DST / "src/main/java/net/montoyo/wd/client/gui").rglob("*.java"):
    text=java.read_text(encoding="utf-8")
    text=text.replace("fillRect(poseStack.bufferSource(),", "fillRect(poseStack,")
    text=text.replace("fillRect(graphics.bufferSource(),", "fillRect(graphics,")
    text=text.replace("fillTexturedRect(poseStack.pose(),", "fillTexturedRect(poseStack,")
    text=text.replace("fillTexturedRect(graphics.pose(),", "fillTexturedRect(graphics,")
    text=text.replace(".drawCenteredString(", ".centeredText(")
    java.write_text(text,encoding="utf-8")

print("GUI and registry 26.2 port pass complete")


# ===========================================================================
# CRITICAL INTERACTION PORT: SCREEN / MINEPAD / WDSCREEN
# ===========================================================================

# EnumProperty factories in 26.2 require the enum class.
for rel in [
    "src/main/java/net/montoyo/wd/block/ScreenThinBlock.java",
    "src/main/java/net/montoyo/wd/block/KeyboardBlockLeft.java",
]:
    p = DST / rel
    if p.exists():
        text = p.read_text(encoding="utf-8")
        text = text.replace(
            'EnumProperty.create("facing", Direction.values())',
            'EnumProperty.create("facing", Direction.class, Direction.values())'
        )
        text = text.replace(
            'EnumProperty.create("facing", Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST)',
            'EnumProperty.create("facing", Direction.class, Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST)'
        )
        p.write_text(text, encoding="utf-8")


# ScreenBlock: preserve the original Shift+RMB URL/config path and empty-hand
# interaction while adapting to the split 26.2 item/empty-hand block API.
screen_block = DST / "src/main/java/net/montoyo/wd/block/ScreenBlock.java"
if screen_block.exists():
    text = screen_block.read_text(encoding="utf-8")
    text = text.replace("import net.minecraft.world.ItemInteractionResult;\n", "")
    if "import net.minecraft.server.level.ServerLevel;" not in text:
        text = text.replace("import net.minecraft.server.level.ServerPlayer;", "import net.minecraft.server.level.ServerPlayer;\nimport net.minecraft.server.level.ServerLevel;")
    if "import net.minecraft.world.level.redstone.Orientation;" not in text:
        text = text.replace("import net.minecraft.world.level.material.FluidState;", "import net.minecraft.world.level.material.FluidState;\nimport net.minecraft.world.level.redstone.Orientation;")

    text = replace_method_by_signature(
        text, "public void onRemove(",
        """    @Override
    protected void affectNeighborsAfterRemoval(BlockState state, ServerLevel level, BlockPos pos, boolean movedByPiston) {
        for (BlockSide value : BlockSide.values()) {
            Vector3i vec = new Vector3i(pos.getX(), pos.getY(), pos.getZ());
            Multiblock.findOrigin(level, vec, value, null);
            BlockPos origin = new BlockPos(vec.x, vec.y, vec.z);
            if (!origin.equals(pos)) {
                level.removeBlockEntity(origin);
                BlockState originState = level.getBlockState(origin);
                if (originState.hasProperty(hasTE))
                    level.setBlock(origin, originState.setValue(hasTE, false), 11);
            }
        }
        super.affectNeighborsAfterRemoval(state, level, pos, movedByPiston);
    }"""
    )

    text = replace_method_by_signature(
        text, "protected InteractionResult useItemOn(",
        """    @Override
    protected InteractionResult useItemOn(ItemStack heldItem, BlockState state, Level world, BlockPos position,
                                          Player player, InteractionHand hand, BlockHitResult hit) {
        if (heldItem.isEmpty())
            return InteractionResult.TRY_WITH_EMPTY_HAND;
        if (!(heldItem.getItem() instanceof IUpgrade) || heldItem.getItem() instanceof ItemLaserPointer)
            return InteractionResult.PASS;
        return handleScreenInteraction(state, world, position, player, hand, hit, heldItem);
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level world, BlockPos position,
                                               Player player, BlockHitResult hit) {
        return handleScreenInteraction(state, world, position, player, InteractionHand.MAIN_HAND, hit, ItemStack.EMPTY);
    }

    private InteractionResult handleScreenInteraction(BlockState state, Level world, BlockPos position,
                                                      Player player, InteractionHand hand, BlockHitResult hit,
                                                      ItemStack heldItem) {
        boolean isUpgrade = !heldItem.isEmpty() && heldItem.getItem() instanceof IUpgrade;

        if (world.isClientSide())
            return InteractionResult.SUCCESS;

        boolean sneaking = player.isShiftKeyDown();
        Vector3i pos = new Vector3i(position);
        BlockSide side = BlockSide.values()[hit.getDirection().ordinal()];

        Multiblock.findOrigin(world, pos, side, null);
        ScreenBlockEntity te = (ScreenBlockEntity) world.getBlockEntity(pos.toBlock());

        if (te != null && te.getScreen(side) != null) {
            ScreenData scr = te.getScreen(side);

            if (sneaking && !isUpgrade) {
                if ((scr.rightsFor(player) & ScreenRights.CHANGE_URL) == 0)
                    Util.toast(player, "restrictions");
                else if (player instanceof ServerPlayer serverPlayer)
                    new SetURLData(pos, scr.side, scr.url).sendTo(serverPlayer);
                return InteractionResult.SUCCESS;
            }

            if (isUpgrade) {
                if (!te.hasUpgrade(side, heldItem)) {
                    if ((scr.rightsFor(player) & ScreenRights.MANAGE_UPGRADES) == 0) {
                        Util.toast(player, "restrictions");
                        return InteractionResult.CONSUME;
                    }
                    if (te.addUpgrade(side, heldItem, player, false)) {
                        if (!player.isCreative()) heldItem.shrink(1);
                        Util.toast(player, ChatFormatting.AQUA, "upgradeOk");
                    } else {
                        Util.toast(player, "upgradeError");
                    }
                }
                return InteractionResult.CONSUME;
            }

            if ((scr.rightsFor(player) & ScreenRights.INTERACT) == 0) {
                Util.toast(player, "restrictions");
                return InteractionResult.CONSUME;
            }

            Vector2i tmp = new Vector2i();
            float hitX = (float) hit.getLocation().x - te.getBlockPos().getX();
            float hitY = (float) hit.getLocation().y - te.getBlockPos().getY();
            float hitZ = (float) hit.getLocation().z - te.getBlockPos().getZ();
            if (hit2pixels(side, hit.getBlockPos(), new Vector3i(hit.getBlockPos()), scr, hitX, hitY, hitZ, tmp))
                te.click(side, tmp);
            return InteractionResult.CONSUME;
        }

        if (isUpgrade)
            return InteractionResult.PASS;

        Vector2i size = Multiblock.measure(world, pos, side);
        if (size.x < 2 && size.y < 2) {
            Util.toast(player, "tooSmall");
            return InteractionResult.SUCCESS;
        }
        if (size.x > CommonConfig.Screen.maxScreenSizeX || size.y > CommonConfig.Screen.maxScreenSizeY) {
            Util.toast(player, "tooBig", CommonConfig.Screen.maxScreenSizeX, CommonConfig.Screen.maxScreenSizeY);
            return InteractionResult.SUCCESS;
        }
        Vector3i err = Multiblock.check(world, pos, size, side);
        if (err != null) {
            Util.toast(player, "invalid", err.toString());
            return InteractionResult.SUCCESS;
        }

        Log.info("Player %s (UUID %s) created a screen at %s of size %dx%d",
                player.getName(), player.getGameProfile().id().toString(), pos.toString(), size.x, size.y);

        if (te == null) {
            BlockPos origin = pos.toBlock();
            world.setBlockAndUpdate(origin, world.getBlockState(origin).setValue(hasTE, true));
            te = (ScreenBlockEntity) world.getBlockEntity(origin);
        }
        if (te != null)
            te.addScreen(side, size, null, player, true);
        return InteractionResult.SUCCESS;
    }"""
    )

    # Current neighborChanged no longer includes the source position.
    text = re.sub(
        r'@Override\s+public void neighborChanged\(BlockState state, Level world, BlockPos pos, Block block, BlockPos source,\s*boolean isMoving\)',
        '@Override\\n    protected void neighborChanged(BlockState state, Level world, BlockPos pos, Block block, Orientation orientation, boolean isMoving)',
        text
    )

    # NeoForge 26.2 supplies the tool ItemStack to onDestroyedByPlayer.
    text = re.sub(
        r'public boolean onDestroyedByPlayer\(BlockState state, Level level, BlockPos pos, Player player,\s*boolean willHarvest, FluidState fluid\)',
        'public boolean onDestroyedByPlayer(BlockState state, Level level, BlockPos pos, Player player,\\n                                       ItemStack tool, boolean willHarvest, FluidState fluid)',
        text
    )
    text = text.replace(
        "super.onDestroyedByPlayer(state, level, pos, player, willHarvest, fluid)",
        "super.onDestroyedByPlayer(state, level, pos, player, tool, willHarvest, fluid)"
    )
    text = text.replace("world.isClientSide", "world.isClientSide()")
    text = text.replace("!world.isClientSide()", "!world.isClientSide()")
    screen_block.write_text(text, encoding="utf-8")


# MinePad: preserve upgraded tooltip, Shift+RMB URL GUI, persistent PadID, and
# throw/break behavior using current Item/CompoundTag contracts.
minepad = DST / "src/main/java/net/montoyo/wd/item/ItemMinePad2.java"
if minepad.exists():
    minepad.write_text("""package net.montoyo.wd.item;

import net.minecraft.ChatFormatting;
import net.minecraft.core.UUIDUtil;
import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.item.component.TooltipDisplay;
import net.minecraft.world.level.Level;
import net.montoyo.wd.WebDisplays;
import net.montoyo.wd.config.CommonConfig;
import net.montoyo.wd.core.CraftComponent;
import net.montoyo.wd.net.WDNetworkRegistry;
import net.montoyo.wd.net.server_bound.C2SMessageMinepadUrl;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;
import java.util.UUID;
import java.util.function.Consumer;

public class ItemMinePad2 extends Item implements WDItem {
    private final boolean upgraded;

    public ItemMinePad2(Properties properties, boolean upgraded) {
        super(properties.stacksTo(1));
        this.upgraded = upgraded;
    }

    public boolean isUpgraded() { return upgraded; }

    @Override
    public void appendHoverText(ItemStack stack, TooltipContext context, TooltipDisplay display,
                                Consumer<Component> tooltip, TooltipFlag flag) {
        super.appendHoverText(stack, context, display, tooltip, flag);
        if (upgraded)
            tooltip.accept(Component.translatable("webdisplays.minepad2.info").withStyle(ChatFormatting.RED));
    }

    private static String getURL(ItemStack stack) {
        CompoundTag tag = stack.getOrDefault(DataComponents.CUSTOM_DATA, CustomData.EMPTY).copyTag();
        return tag.isEmpty() || !tag.contains("PadURL")
                ? CommonConfig.Browser.homepage
                : tag.getStringOr("PadURL", CommonConfig.Browser.homepage);
    }

    private static UUID readPadId(CompoundTag tag) {
        return tag.read("PadID", UUIDUtil.CODEC).orElse(new UUID(0L, 0L));
    }

    @Override
    @Nonnull
    public InteractionResult use(Level world, Player player, @Nonnull InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);

        if (player.isShiftKeyDown()) {
            if (world.isClientSide())
                WebDisplays.PROXY.displaySetPadURLGui(stack, getURL(stack));
            return InteractionResult.SUCCESS;
        }

        CompoundTag tag = stack.getOrDefault(DataComponents.CUSTOM_DATA, CustomData.EMPTY).copyTag();
        if (!tag.isEmpty() && tag.contains("PadID")) {
            if (world.isClientSide())
                WebDisplays.PROXY.openMinePadGui(readPadId(tag));
            return InteractionResult.SUCCESS;
        }

        UUID uuid = UUID.randomUUID();
        String url = getURL(stack);
        if (world.isClientSide())
            WDNetworkRegistry.sendToServer(new C2SMessageMinepadUrl(uuid, url));

        CompoundTag newTag = new CompoundTag();
        newTag.store("PadID", UUIDUtil.CODEC, uuid);
        newTag.putString("PadURL", url);
        stack.set(DataComponents.CUSTOM_DATA, CustomData.of(newTag));
        return InteractionResult.SUCCESS;
    }

    @Override
    public boolean onEntityItemUpdate(ItemStack stack, ItemEntity entity) {
        if (entity.onGround() && !entity.level().isClientSide()) {
            CompoundTag tag = entity.getItem().getOrDefault(DataComponents.CUSTOM_DATA, CustomData.EMPTY).copyTag();
            if (!tag.isEmpty() && tag.contains("ThrowHeight")) {
                double height = tag.getDoubleOr("ThrowHeight", 0.0);
                UUID thrower = null;
                if (tag.contains("ThrowerMSB") && tag.contains("ThrowerLSB"))
                    thrower = new UUID(tag.getLongOr("ThrowerMSB", 0L), tag.getLongOr("ThrowerLSB", 0L));

                if (tag.contains("PadID") || tag.contains("PadURL")) {
                    tag.remove("ThrowerMSB");
                    tag.remove("ThrowerLSB");
                    tag.remove("ThrowHeight");
                    entity.getItem().set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
                } else {
                    entity.getItem().remove(DataComponents.CUSTOM_DATA);
                }

                if (thrower != null && height - entity.getBlockY() >= 20.0) {
                    entity.level().playSound(null, entity.getBlockX(), entity.getBlockY(), entity.getBlockZ(),
                            SoundEvents.GLASS_BREAK, SoundSource.BLOCKS, 4.0f, 1.0f);
                    entity.level().addFreshEntity(new ItemEntity(entity.level(), entity.getBlockX(), entity.getBlockY(),
                            entity.getBlockZ(), CraftComponent.EXTCARD.makeItemStack()));
                    entity.setRemoved(Entity.RemovalReason.CHANGED_DIMENSION);
                }
            }
        }
        return false;
    }

    @Nullable
    @Override
    public String getWikiName(@Nonnull ItemStack stack) {
        return stack.getItem().getName(stack).getString();
    }
}
""", encoding="utf-8")


# WDScreen modern event bridge cleanup: primitive overloads are internal helpers,
# only event-object overloads override Minecraft 26.2.
wdscreen = DST / "src/main/java/net/montoyo/wd/client/gui/WDScreen.java"
if wdscreen.exists():
    text = wdscreen.read_text(encoding="utf-8")
    text = text.replace("import com.mojang.blaze3d.systems.RenderSystem;\n", "")
    text = text.replace("RenderSystem.setShaderColor(1.f, 1.f, 1.f, 1.f);\n", "")
    text = text.replace("renderBackground(poseStack, mouseX, mouseY, ptt);", "extractBackground(poseStack, mouseX, mouseY, ptt);")
    text = text.replace("return up || super.keyReleased(keyCode, scanCode, modifiers);", "return up;")
    text = re.sub(
        r'@Override\s+public void resize\(Minecraft minecraft, int width, int height\)',
        '@Override\\n    public void resize(int width, int height)',
        text
    )
    text = text.replace("super.resize(minecraft, width, height);", "super.resize(width, height);")
    text = text.replace("minecraft.setScreen(", "minecraft.gui.setScreen(")
    text = text.replace("poseStack.renderTooltip(Minecraft.getInstance().font, is, x, y);",
                        "poseStack.setTooltipForNextFrame(Minecraft.getInstance().font, is, x, y);")
    text = text.replace("poseStack.renderTooltip(Minecraft.getInstance().font, lines.stream().map(a -> FormattedCharSequence.forward(a, Style.EMPTY)).collect(Collectors.toList()), x, y);",
                        "poseStack.setTooltipForNextFrame(Minecraft.getInstance().font, lines.stream().map(a -> FormattedCharSequence.forward(a, Style.EMPTY)).collect(Collectors.toList()), x, y);")

    # Remove @Override only from the legacy primitive helper signatures.
    for signature in [
        "public boolean charTyped(char codePoint, int modifiers)",
        "public boolean mouseClicked(double mouseX, double mouseY, int button)",
        "public boolean mouseReleased(double mouseX, double mouseY, int button)",
        "public boolean mouseDragged(double mouseX, double mouseY, int button, double dragX, double dragY)",
        "public boolean keyPressed(int keyCode, int scanCode, int modifiers)",
        "public boolean keyReleased(int keyCode, int scanCode, int modifiers)",
    ]:
        text = text.replace("    @Override\n    " + signature, "    " + signature)

    wdscreen.write_text(text, encoding="utf-8")


# Remove obsolete crosshair mixin entirely for compile isolation. The actual HUD
# cursor gets a dedicated 26.2 state hook later, not a call to deleted immediate
# rendering code.
overlay_mixin = DST / "src/main/java/net/montoyo/wd/mixins/OverlayMixin.java"
if overlay_mixin.exists():
    overlay_mixin.write_text("""package net.montoyo.wd.mixins;
/** 26.2 placeholder; legacy immediate HUD injection was removed. */
public final class OverlayMixin {}
""", encoding="utf-8")

# Remove it from mixin config so an empty placeholder is never applied.
mixin_json = DST / "src/main/resources/webdisplays.mixins.json"
if mixin_json.exists():
    import json
    data = json.loads(mixin_json.read_text(encoding="utf-8"))
    for key in ("client", "mixins"):
        if key in data and isinstance(data[key], list):
            data[key] = [x for x in data[key] if "OverlayMixin" not in x]
    mixin_json.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


# Final sanity checks: if these fail, stop in PREPARE instead of feeding stale
# 1.21 render code to javac and pretending the next 100 errors are new.
sanity = {
    "client/gui/controls/Control.java": ["Tesselator", "BufferUploader", "RenderSystem.setShader"],
    "client/gui/controls/List.java": ["MultiBufferSource", "TextureTarget"],
    "client/gui/controls/UpgradeGroup.java": ["renderer.entity.ItemRenderer"],
    "client/gui/GuiMinePad.java": ["BufferUploader", "Tesselator.getInstance"],
}
for rel, forbidden in sanity.items():
    p = DST / "src/main/java/net/montoyo/wd" / rel
    if not p.exists():
        raise RuntimeError("Missing generated sanity target: " + str(p))
    generated = p.read_text(encoding="utf-8")
    bad = [token for token in forbidden if token in generated]
    if bad:
        raise RuntimeError(f"Stale 1.21 render API in {rel}: {bad}")

print("Critical interaction port and sanity checks complete")


# ===========================================================================
# BLOCK API CLEANUP
# ===========================================================================

# Mechanical guard against repeated client-side accessor migration.
for java in (DST / "src/main/java").rglob("*.java"):
    text = java.read_text(encoding="utf-8")
    while ".isClientSide()()" in text:
        text = text.replace(".isClientSide()()", ".isClientSide()")
    java.write_text(text, encoding="utf-8")


# Peripheral blocks: use the current InteractionResult directly and provide the
# empty-hand path explicitly.
peripheral = DST / "src/main/java/net/montoyo/wd/block/PeripheralBlock.java"
if peripheral.exists():
    text = peripheral.read_text(encoding="utf-8")
    text = text.replace("import net.minecraft.world.ItemInteractionResult;\n", "")
    if "import net.minecraft.world.level.redstone.Orientation;" not in text:
        text = text.replace("import net.minecraft.world.level.material.PushReaction;",
                            "import net.minecraft.world.level.material.PushReaction;\nimport net.minecraft.world.level.redstone.Orientation;")
    text = replace_method_by_signature(
        text, "protected InteractionResult useItemOn(",
        """    @Override
    protected InteractionResult useItemOn(ItemStack stack, BlockState state, Level world, BlockPos pos,
                                          Player player, InteractionHand hand, BlockHitResult hit) {
        if (player.isShiftKeyDown() || stack.getItem() instanceof ItemLinker)
            return InteractionResult.PASS;
        return interact(world, pos, player, hand);
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level world, BlockPos pos,
                                               Player player, BlockHitResult hit) {
        if (player.isShiftKeyDown())
            return InteractionResult.PASS;
        return interact(world, pos, player, InteractionHand.MAIN_HAND);
    }

    private InteractionResult interact(Level world, BlockPos pos, Player player, InteractionHand hand) {
        BlockEntity te = world.getBlockEntity(pos);
        if (te instanceof AbstractPeripheralBlockEntity peripheral)
            return peripheral.onRightClick(player, hand);
        if (te instanceof ServerBlockEntity server) {
            server.onPlayerRightClick(player);
            return InteractionResult.SUCCESS;
        }
        return InteractionResult.PASS;
    }"""
    )
    text = re.sub(
        r'@Override\s+public void neighborChanged\(BlockState state, Level world, BlockPos pos, Block neighborType, BlockPos neighbor, boolean isMoving\)',
        '@Override\\n    protected void neighborChanged(BlockState state, Level world, BlockPos pos, Block neighborType, Orientation orientation, boolean isMoving)',
        text
    )
    text = text.replace("onNeighborChange(neighborType, neighbor)", "onNeighborChange(neighborType, pos)")
    text = text.replace("world.isClientSide", "world.isClientSide()")
    while ".isClientSide()()" in text:
        text = text.replace(".isClientSide()()", ".isClientSide()")
    peripheral.write_text(text, encoding="utf-8")


# Both keyboard halves use current empty-hand/item interaction and modern
# removal hook, while retaining paired-half cleanup.
keyboard_left = DST / "src/main/java/net/montoyo/wd/block/KeyboardBlockLeft.java"
if keyboard_left.exists():
    text = keyboard_left.read_text(encoding="utf-8")
    text = text.replace("import net.minecraft.world.ItemInteractionResult;\n", "")
    if "import net.minecraft.server.level.ServerLevel;" not in text:
        text = text.replace("import net.minecraft.core.Direction;", "import net.minecraft.core.Direction;\nimport net.minecraft.server.level.ServerLevel;")
    text = replace_method_by_signature(
        text, "protected @NotNull InteractionResult useItemOn(",
        """    @Override
    protected @NotNull InteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos,
                                                   Player player, InteractionHand hand, BlockHitResult hit) {
        if (stack.getItem() instanceof ItemLinker)
            return InteractionResult.PASS;
        KeyboardBlockEntity keyboard = getTileEntity(state, level, pos);
        return keyboard == null ? InteractionResult.PASS : keyboard.onRightClick(player, hand);
    }

    @Override
    protected @NotNull InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos,
                                                        Player player, BlockHitResult hit) {
        KeyboardBlockEntity keyboard = getTileEntity(state, level, pos);
        return keyboard == null ? InteractionResult.PASS : keyboard.onRightClick(player, InteractionHand.MAIN_HAND);
    }"""
    )
    text = replace_method_by_signature(
        text, "public void onRemove(",
        """    @Override
    protected void affectNeighborsAfterRemoval(BlockState state, ServerLevel level, BlockPos pos, boolean movedByPiston) {
        remove(state, level, pos, false, false);
        super.affectNeighborsAfterRemoval(state, level, pos, movedByPiston);
    }"""
    )
    text = text.replace("world.isClientSide", "world.isClientSide()")
    while ".isClientSide()()" in text:
        text = text.replace(".isClientSide()()", ".isClientSide()")
    keyboard_left.write_text(text, encoding="utf-8")


keyboard_right = DST / "src/main/java/net/montoyo/wd/block/KeyboardBlockRight.java"
if keyboard_right.exists():
    text = keyboard_right.read_text(encoding="utf-8")
    text = text.replace("import net.minecraft.world.ItemInteractionResult;\n", "")
    if "import net.minecraft.server.level.ServerLevel;" not in text:
        text = text.replace("import net.minecraft.core.BlockPos;", "import net.minecraft.core.BlockPos;\nimport net.minecraft.server.level.ServerLevel;")
    text = replace_method_by_signature(
        text, "protected @NotNull InteractionResult useItemOn(",
        """    @Override
    protected @NotNull InteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos,
                                                   Player player, InteractionHand hand, BlockHitResult hit) {
        if (stack.getItem() instanceof ItemLinker)
            return InteractionResult.PASS;
        KeyboardBlockEntity keyboard = KeyboardBlockLeft.getTileEntity(state, level, pos);
        return keyboard == null ? InteractionResult.PASS : keyboard.onRightClick(player, hand);
    }

    @Override
    protected @NotNull InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos,
                                                        Player player, BlockHitResult hit) {
        KeyboardBlockEntity keyboard = KeyboardBlockLeft.getTileEntity(state, level, pos);
        return keyboard == null ? InteractionResult.PASS : keyboard.onRightClick(player, InteractionHand.MAIN_HAND);
    }"""
    )
    text = replace_method_by_signature(
        text, "public void onRemove(",
        """    @Override
    protected void affectNeighborsAfterRemoval(BlockState state, ServerLevel level, BlockPos pos, boolean movedByPiston) {
        remove(state, level, pos, false, false);
        super.affectNeighborsAfterRemoval(state, level, pos, movedByPiston);
    }"""
    )
    text = text.replace("world.isClientSide", "world.isClientSide()")
    while ".isClientSide()()" in text:
        text = text.replace(".isClientSide()()", ".isClientSide()")
    keyboard_right.write_text(text, encoding="utf-8")


# Direct, deterministic 26.2 block-entity registry. Avoid regex conversion.
tile = DST / "src/main/java/net/montoyo/wd/registry/TileRegistry.java"
tile.write_text("""package net.montoyo.wd.registry;

import net.minecraft.core.registries.Registries;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;
import net.montoyo.wd.entity.*;

import java.util.Set;

public final class TileRegistry {
    public static final DeferredRegister<BlockEntityType<?>> TILE_TYPES =
            DeferredRegister.create(Registries.BLOCK_ENTITY_TYPE, "webdisplays");

    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<ScreenBlockEntity>> SCREEN_BLOCK_ENTITY =
            TILE_TYPES.register("screen", () -> new BlockEntityType<>(
                    ScreenBlockEntity::new,
                    Set.of(BlockRegistry.SCREEN_BLOCk.get(), BlockRegistry.SCREEN_THIN_BLOCK.get())));

    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<KeyboardBlockEntity>> KEYBOARD =
            TILE_TYPES.register("kb_left", () -> new BlockEntityType<>(
                    KeyboardBlockEntity::new, Set.of(BlockRegistry.KEYBOARD_BLOCK.get())));

    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<RemoteControlBlockEntity>> REMOTE_CONTROLLER =
            TILE_TYPES.register("rctrl", () -> new BlockEntityType<>(
                    RemoteControlBlockEntity::new, Set.of(BlockRegistry.REMOTE_CONTROLLER_BLOCK.get())));

    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<RedstoneControlBlockEntity>> REDSTONE_CONTROLLER =
            TILE_TYPES.register("redctrl", () -> new BlockEntityType<>(
                    RedstoneControlBlockEntity::new, Set.of(BlockRegistry.REDSTONE_CONTROL_BLOCK.get())));

    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<ServerBlockEntity>> SERVER =
            TILE_TYPES.register("server", () -> new BlockEntityType<>(
                    ServerBlockEntity::new, Set.of(BlockRegistry.SERVER_BLOCK.get())));

    private TileRegistry() {}

    public static void init(IEventBus bus) {
        TILE_TYPES.register(bus);
    }
}
""", encoding="utf-8")

print("Block API cleanup complete")
