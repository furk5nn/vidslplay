package com.furk5nn.videoscreen.registry;

import com.furk5nn.videoscreen.VideoScreenMod;
import com.furk5nn.videoscreen.block.VideoScreenBlock;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.material.MapColor;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.registries.DeferredBlock;
import net.neoforged.neoforge.registries.DeferredRegister;

public final class ModBlocks {
    public static final DeferredRegister.Blocks BLOCKS = DeferredRegister.createBlocks(VideoScreenMod.MOD_ID);

    public static final DeferredBlock<VideoScreenBlock> VIDEO_SCREEN = BLOCKS.registerBlock(
        "video_screen",
        VideoScreenBlock::new,
        p -> p.mapColor(MapColor.COLOR_BLACK).strength(2.0F).sound(SoundType.METAL).noOcclusion()
    );

    public static void register(IEventBus bus) { BLOCKS.register(bus); }
    private ModBlocks() {}
}
