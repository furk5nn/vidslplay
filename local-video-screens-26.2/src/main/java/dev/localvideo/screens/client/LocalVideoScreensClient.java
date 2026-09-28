package dev.localvideo.screens.client;

import dev.localvideo.screens.LocalVideoScreens;
import net.minecraft.client.Minecraft;
import net.minecraft.network.chat.Component;
import net.minecraft.world.InteractionResult;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.ModContainer;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.client.event.ClientTickEvent;
import net.neoforged.neoforge.client.event.SubmitCustomGeometryEvent;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent;

@Mod(value = LocalVideoScreens.MOD_ID, dist = Dist.CLIENT)
public final class LocalVideoScreensClient {
    public LocalVideoScreensClient(IEventBus modBus, ModContainer container) {
        NeoForge.EVENT_BUS.addListener(this::onRightClickBlock);
        NeoForge.EVENT_BUS.addListener(this::onClientTick);
        NeoForge.EVENT_BUS.addListener(this::onSubmitGeometry);
    }

    private void onRightClickBlock(PlayerInteractEvent.RightClickBlock event) {
        if (!event.getLevel().getBlockState(event.getPos()).is(LocalVideoScreens.SCREEN_BLOCK.get())) return;
        if (!event.getLevel().isClientSide()) return;

        event.setCanceled(true);
        event.setCancellationResult(InteractionResult.SUCCESS);

        Minecraft mc = Minecraft.getInstance();

        if (!event.getEntity().isShiftKeyDown()) {
            VideoScreenManager.get().browserClick(
                    event.getLevel(),
                    event.getPos(),
                    event.getHitVec().getDirection(),
                    event.getHitVec().getLocation()
            );
            return;
        }

        var result = ScreenGeometry.discover(event.getLevel(), event.getPos(), event.getHitVec().getDirection());
        if (!result.success()) {
            if (mc.player != null) mc.player.sendSystemMessage(Component.literal(result.error()));
            return;
        }
        mc.gui.setScreen(new VideoSelectScreen(result.geometry()));
    }

    private void onClientTick(ClientTickEvent.Post event) {
        VideoScreenManager.get().clientTick();
    }

    private void onSubmitGeometry(SubmitCustomGeometryEvent event) {
        VideoScreenManager.get().submitGeometry(event);
    }
}
