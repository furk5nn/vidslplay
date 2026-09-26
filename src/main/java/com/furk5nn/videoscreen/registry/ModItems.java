package com.furk5nn.videoscreen.registry;

import com.furk5nn.videoscreen.VideoScreenMod;
import net.minecraft.world.item.BlockItem;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.registries.DeferredItem;
import net.neoforged.neoforge.registries.DeferredRegister;

public final class ModItems {
    public static final DeferredRegister.Items ITEMS = DeferredRegister.createItems(VideoScreenMod.MOD_ID);
    public static final DeferredItem<BlockItem> VIDEO_SCREEN = ITEMS.registerSimpleBlockItem(ModBlocks.VIDEO_SCREEN);
    public static void register(IEventBus bus) { ITEMS.register(bus); }
    private ModItems() {}
}
