package com.furk5nn.videoscreen.client;

import de.keksuccino.rinku.Rinku;
import de.keksuccino.rinku.RinkuBrowser;
import java.io.File;
import net.minecraft.client.Minecraft;
import net.minecraft.resources.Identifier;

public final class WaterMediaVideoPlayer implements AutoCloseable {
    private static final int MAX_TEXTURE_WIDTH = 1280;
    private static final int MAX_TEXTURE_HEIGHT = 720;
    private static final int TARGET_FPS = 30;

    private final File source;
    private final int panelWidth;
    private final int panelHeight;
    private RinkuBrowser browser;
    private boolean closed;
    private String error;

    public WaterMediaVideoPlayer(File source, int panelWidth, int panelHeight) {
        this.source = source.getAbsoluteFile();
        this.panelWidth = Math.max(1, panelWidth);
        this.panelHeight = Math.max(1, panelHeight);
    }

    public void tickInit() {
        if (closed || browser != null || error != null) return;

        if (!Rinku.isInitialized()) {
            Rinku.scheduleForInit(success -> Minecraft.getInstance().execute(() -> {
                if (closed || browser != null || error != null) return;
                if (success) {
                    createBrowser();
                } else {
                    error = "Rinku could not initialize Chromium";
                }
            }));
            return;
        }

        createBrowser();
    }

    private void createBrowser() {
        if (closed || browser != null) return;
        try {
            int[] size = chooseTextureSize(panelWidth, panelHeight);
            browser = Rinku.createBrowser("about:blank", false, size[0], size[1]);
            browser.useBrowserControls(false);
            browser.setWindowlessFrameRate(TARGET_FPS);
            browser.loadURL(source.toURI().toASCIIString());
        } catch (Throwable t) {
            t.printStackTrace();
            error = "Rinku browser error: " + t.getClass().getSimpleName();
            close();
        }
    }

    public boolean isReady() {
        tickInit();
        return browser != null && browser.isTextureReady();
    }

    public Identifier texture() {
        return isReady() ? browser.getTextureIdentifier() : null;
    }

    public String error() {
        return error;
    }

    public File source() {
        return source;
    }

    public RinkuBrowser browser() {
        return browser;
    }

    public void styleVideoDocument() {
        if (browser == null || closed) return;
        String js = """
            (() => {
              document.documentElement.style.cssText='margin:0;width:100%;height:100%;background:#000;overflow:hidden';
              document.body.style.cssText='margin:0;width:100%;height:100%;background:#000;overflow:hidden';
              const v=document.querySelector('video');
              if(v){
                v.style.cssText='position:fixed;inset:0;width:100%;height:100%;object-fit:contain;background:#000';
                v.controls=false;
                v.autoplay=true;
                v.loop=false;
                v.volume=1.0;
                const p=v.play(); if(p) p.catch(()=>{});
              }
            })();
            """;
        browser.executeJavaScript(js, browser.getURL(), 0);
    }

    @Override
    public void close() {
        if (closed) return;
        closed = true;
        RinkuBrowser old = browser;
        browser = null;
        if (old != null) {
            try { old.close(); } catch (Throwable ignored) {}
        }
    }

    private static int[] chooseTextureSize(int blocksWide, int blocksHigh) {
        double aspect = Math.max(0.1, blocksWide / (double) Math.max(1, blocksHigh));
        int width = MAX_TEXTURE_WIDTH;
        int height = (int) Math.round(width / aspect);
        if (height > MAX_TEXTURE_HEIGHT) {
            height = MAX_TEXTURE_HEIGHT;
            width = (int) Math.round(height * aspect);
        }
        width = Math.max(320, Math.min(MAX_TEXTURE_WIDTH, width));
        height = Math.max(180, Math.min(MAX_TEXTURE_HEIGHT, height));
        return new int[]{width, height};
    }
}
