package dev.localvideo.screens.client;

import de.keksuccino.rinku.Rinku;
import de.keksuccino.rinku.RinkuBrowser;
import net.minecraft.client.Minecraft;
import net.minecraft.resources.Identifier;

import java.io.File;

final class VideoSession {
    private static final int MAX_TEXTURE_WIDTH = 1280;
    private static final int MAX_TEXTURE_HEIGHT = 720;
    private static final int TARGET_FPS = 30;

    private final ScreenGeometry geometry;
    private final File file;
    private RinkuBrowser browser;
    private boolean closed;

    VideoSession(ScreenGeometry geometry, File file) {
        this.geometry = geometry;
        this.file = file;
    }

    ScreenGeometry geometry() {
        return geometry;
    }

    void start() {
        if (closed) return;
        if (Rinku.isInitialized()) {
            createBrowser();
        } else {
            Rinku.scheduleForInit(success -> Minecraft.getInstance().execute(() -> {
                if (!closed && success) createBrowser();
            }));
        }
    }

    private void createBrowser() {
        if (closed || browser != null) return;

        int[] size = chooseTextureSize(geometry.width(), geometry.height());
        browser = Rinku.createBrowser("about:blank", false);
        browser.resize(size[0], size[1]);
        browser.setWindowlessFrameRate(TARGET_FPS);
        VideoScreenManager.get().bindBrowser(this, browser);
        browser.loadURL(file.toURI().toASCIIString());
    }

    void styleVideoDocument() {
        if (closed || browser == null) return;
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

    Identifier texture() {
        return browser != null && browser.isTextureReady() ? browser.getTextureIdentifier() : null;
    }

    RinkuBrowser browser() {
        return browser;
    }

    void close() {
        if (closed) return;
        closed = true;
        RinkuBrowser old = browser;
        browser = null;
        if (old != null) {
            VideoScreenManager.get().unbindBrowser(old);
            old.close();
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
