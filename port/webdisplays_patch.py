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
