package com.furk5nn.videoscreen.client;

import com.cinemamod.mcef.MCEF;
import com.cinemamod.mcef.MCEFBrowser;
import java.io.File;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import net.minecraft.resources.Identifier;

public final class ChromiumVideoPlayer implements AutoCloseable {
    private final File source;
    private final Path htmlFile;
    private MCEFBrowser browser;
    private boolean paused;
    private int width;
    private int height;

    public ChromiumVideoPlayer(File source, int width, int height) throws IOException {
        this.source = source;
        this.htmlFile = Files.createTempFile("videoscreen-", ".html");

        String videoUri = source.toURI().toASCIIString().replace("&", "&amp;").replace("\"", "&quot;");
        String html = """
            <!doctype html>
            <html>
            <head>
              <meta charset="utf-8">
              <style>
                html,body{margin:0;width:100%%;height:100%%;overflow:hidden;background:#000}
                video{display:block;width:100%%;height:100%%;object-fit:contain;background:#000}
              </style>
            </head>
            <body>
              <video id="v" src="%s" autoplay loop controls playsinline></video>
              <script>
                const v=document.getElementById('v');
                v.volume=1.0;
                v.play().catch(()=>{});
              </script>
            </body>
            </html>
            """.formatted(videoUri);
        Files.writeString(htmlFile, html, StandardCharsets.UTF_8);

        if (!MCEF.isInitialized()) {
            throw new IllegalStateException("Rinku/MCEF is not initialized yet");
        }

        this.width = Math.max(320, width);
        this.height = Math.max(180, height);
        browser = MCEF.createBrowser(htmlFile.toUri().toASCIIString(), false, this.width, this.height);
        browser.useBrowserControls(false);
        browser.setFocus(false);
    }

    public void resize(int width, int height) {
        int newWidth = Math.max(320, width);
        int newHeight = Math.max(180, height);
        if (browser != null && (newWidth != this.width || newHeight != this.height)) {
            this.width = newWidth;
            this.height = newHeight;
            browser.resize(newWidth, newHeight);
        }
    }

    public boolean isReady() {
        return browser != null && browser.isTextureReady();
    }

    public Identifier texture() {
        return browser == null ? null : browser.getTextureIdentifier();
    }

    public void togglePause() {
        if (browser == null) return;
        paused = !paused;
        String js = paused
            ? "(()=>{const v=document.getElementById('v');if(v)v.pause();})()"
            : "(()=>{const v=document.getElementById('v');if(v)v.play().catch(()=>{});})()";
        browser.executeJavaScript(js, browser.getURL(), 0);
    }

    public boolean isPaused() {
        return paused;
    }

    public File source() {
        return source;
    }

    @Override
    public void close() {
        if (browser != null) {
            browser.close();
            browser = null;
        }
        try {
            Files.deleteIfExists(htmlFile);
        } catch (IOException ignored) {
        }
    }
}
