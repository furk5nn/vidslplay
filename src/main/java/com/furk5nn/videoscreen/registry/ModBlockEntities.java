package com.furk5nn.videoscreen.registry;

import com.furk5nn.videoscreen.VideoScreenMod;
import com.furk5nn.videoscreen.block.VideoScreenBlockEntity;
import net.minecraft.core.registries.Registries;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;

public final class ModBlockEntities {
    public static final DeferredRegister<BlockEntityType<?>> TYPES =
        DeferredRegister.create(Registries.BLOCK_ENTITY_TYPE, VideoScreenMod.MOD_ID);

    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<VideoScreenBlockEntity>> VIDEO_SCREEN =
        TYPES.register("video_screen", () -> new BlockEntityType<>(
            VideoScreenBlockEntity::new, ModBlocks.VIDEO_SCREEN.get()
        ));

    public static void register(IEventBus bus) { TYPES.register(bus); }
    private ModBlockEntities() {}
}
