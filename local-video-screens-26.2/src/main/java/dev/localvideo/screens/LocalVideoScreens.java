package dev.localvideo.screens;

import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.CreativeModeTabs;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.MapColor;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.ModContainer;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.event.BuildCreativeModeTabContentsEvent;
import net.neoforged.neoforge.registries.DeferredBlock;
import net.neoforged.neoforge.registries.DeferredItem;
import net.neoforged.neoforge.registries.DeferredRegister;

@Mod(LocalVideoScreens.MOD_ID)
public final class LocalVideoScreens {
    public static final String MOD_ID = "localvideoscreens";

    public static final DeferredRegister.Blocks BLOCKS = DeferredRegister.createBlocks(MOD_ID);
    public static final DeferredRegister.Items ITEMS = DeferredRegister.createItems(MOD_ID);

    public static final DeferredBlock<Block> SCREEN_BLOCK = BLOCKS.registerSimpleBlock(
            "screen_block",
            props -> props.mapColor(MapColor.COLOR_BLACK).strength(1.5F).noOcclusion()
    );

    public static final DeferredItem<BlockItem> SCREEN_BLOCK_ITEM = ITEMS.registerSimpleBlockItem("screen_block", SCREEN_BLOCK);

    public LocalVideoScreens(IEventBus modBus, ModContainer container) {
        BLOCKS.register(modBus);
        ITEMS.register(modBus);
        modBus.addListener(this::addCreative);
    }

    private void addCreative(BuildCreativeModeTabContentsEvent event) {
        if (event.getTabKey() == CreativeModeTabs.BUILDING_BLOCKS) {
            event.accept(SCREEN_BLOCK_ITEM);
        }
    }
}
