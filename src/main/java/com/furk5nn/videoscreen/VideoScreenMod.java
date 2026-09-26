package com.furk5nn.videoscreen;

import com.furk5nn.videoscreen.registry.ModBlockEntities;
import com.furk5nn.videoscreen.registry.ModBlocks;
import com.furk5nn.videoscreen.registry.ModItems;
import net.minecraft.world.item.CreativeModeTabs;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.event.BuildCreativeModeTabContentsEvent;

@Mod(VideoScreenMod.MOD_ID)
public final class VideoScreenMod {
    public static final String MOD_ID = "videoscreen";

    public VideoScreenMod(IEventBus modBus) {
        ModBlocks.register(modBus);
        ModItems.register(modBus);
        ModBlockEntities.register(modBus);
        modBus.addListener(VideoScreenMod::addCreativeItems);
    }

    private static void addCreativeItems(BuildCreativeModeTabContentsEvent event) {
        if (event.getTabKey() == CreativeModeTabs.FUNCTIONAL_BLOCKS) {
            event.accept(ModItems.VIDEO_SCREEN);
        }
    }
}
