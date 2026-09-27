package com.furk5nn.videoscreen.client;

import de.keksuccino.rinku.Rinku;
import de.keksuccino.rinku.RinkuBrowser;

import java.io.File;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

import net.minecraft.resources.Identifier;

public final class ChromiumVideoPlayer implements AutoCloseable {
    private final File source;
    private final Path htmlFile;
    private final LocalVideoHttpServer mediaServer;
    private RinkuBrowser browser;
    private boolean paused;
    private int width;
    private int height;

    public ChromiumVideoPlayer(File source, int width, int height) throws IOException {
        this.source = source.getCanonicalFile();

        if (!Rinku.isInitialized()) {
            throw new IllegalStateException("Rinku is not initialized yet");
        }

        this.mediaServer = new LocalVideoHttpServer(this.source);
        this.htmlFile = Files.createTempFile("videoscreen-", ".html");

        String mediaUrl = mediaServer.uri().toASCIIString();

        String html = """
            <!doctype html>
            <html>
            <head>
              <meta charset="utf-8">
              <style>
                html,body{margin:0;width:100%%;height:100%%;overflow:hidden;background:#000;color:#fff;font-family:sans-serif}
                #wrap{position:relative;width:100%%;height:100%%;background:#000}
                video{display:block;width:100%%;height:100%%;object-fit:contain;background:#000}
                #err{position:absolute;left:12px;top:12px;right:12px;padding:10px;background:rgba(120,0,0,.82);font-size:16px;display:none;white-space:pre-wrap}
              </style>
            </head>
            <body>
              <div id="wrap">
                <video id="v" autoplay loop controls playsinline preload="auto"></video>
                <div id="err"></div>
              </div>
              <script>
                const source='%s';
                const v=document.getElementById('v');
                const err=document.getElementById('err');

                function show(msg){
                  err.textContent=msg;
                  err.style.display='block';
                  console.error('[VideoScreen] '+msg);
                }

                function start(){
                  v.src=source;
                  v.loop=true;
                  v.volume=1.0;
                  v.load();
                  const p=v.play();
                  if(p && p.catch) p.catch(e=>show('PLAY FAILED: '+e.name+' - '+e.message));
                }

                v.addEventListener('loadedmetadata', ()=>{
                  err.style.display='none';
                  console.log('[VideoScreen] metadata '+v.videoWidth+'x'+v.videoHeight+' duration='+v.duration);
                });
                v.addEventListener('canplay', ()=>console.log('[VideoScreen] canplay'));
                v.addEventListener('playing', ()=>console.log('[VideoScreen] playing'));
                v.addEventListener('error', ()=>{
                  let code=v.error ? v.error.code : 0;
                  let label = code===1?'ABORTED':code===2?'NETWORK':code===3?'DECODE':code===4?'FORMAT_NOT_SUPPORTED':'UNKNOWN';
                  show('MEDIA ERROR '+code+' ('+label+')\\n'+source);
                });

                start();
              </script>
            </body>
            </html>
            """.formatted(mediaUrl);

        Files.writeString(htmlFile, html, StandardCharsets.UTF_8);

        this.width = Math.max(320, width);
        this.height = Math.max(180, height);
        browser = Rinku.createBrowser(htmlFile.toUri().toASCIIString(), false);
        browser.resize(this.width, this.height);
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
        return browser != null && browser.getTextureIdentifier() != null;
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
        mediaServer.close();
        try {
            Files.deleteIfExists(htmlFile);
        } catch (IOException ignored) {
        }
    }
}
