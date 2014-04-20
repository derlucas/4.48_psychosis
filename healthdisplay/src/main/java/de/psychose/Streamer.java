package de.psychose;

import org.jboss.netty.bootstrap.ServerBootstrap;
import org.jboss.netty.buffer.ChannelBuffers;
import org.jboss.netty.channel.*;
import org.jboss.netty.channel.socket.nio.NioServerSocketChannelFactory;
import org.jboss.netty.handler.codec.frame.TooLongFrameException;
import org.jboss.netty.handler.codec.http.*;
import org.jboss.netty.handler.stream.ChunkedInput;
import org.jboss.netty.handler.stream.ChunkedWriteHandler;
import org.jboss.netty.util.CharsetUtil;

import javax.imageio.ImageIO;
import java.awt.*;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.channels.ClosedChannelException;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;

import static org.jboss.netty.handler.codec.http.HttpHeaders.Names.CONTENT_TYPE;
import static org.jboss.netty.handler.codec.http.HttpMethod.GET;
import static org.jboss.netty.handler.codec.http.HttpResponseStatus.*;
import static org.jboss.netty.handler.codec.http.HttpVersion.HTTP_1_1;

/**
 * @author Maurus Cuelenaere <mcuelenaere@gmail.com>
 *         taken from http://blog.maurus.be/2012/05/09/netty-mjpeg-streamer/
 */
public class Streamer {
    private final int port;
    private final Component view;
    private final ViewRenderer renderer;

    private class ViewRenderer implements Runnable {
        private final BufferedImage image;
        private final AtomicReference<byte[]> currentBuffer;
        private final AtomicInteger listenerCount;
        private final int napTime;
        private final ByteArrayOutputStream outputStream;

        public ViewRenderer() {
            this(10);
        }

        public ViewRenderer(int fps) {
            this.napTime = 1000 / fps;
            this.listenerCount = new AtomicInteger();
            this.currentBuffer = new AtomicReference<byte[]>();
            this.image = new BufferedImage(view.getWidth(), view.getHeight(), BufferedImage.TYPE_INT_RGB);
            this.outputStream = new ByteArrayOutputStream();
        }

        @Override
        public void run() {
            while (!Thread.interrupted()) {
                long sleepTill = System.currentTimeMillis() + napTime;

                if (listenerCount.get() > 0) {
                    Graphics g = image.createGraphics();
                    view.paint(g);
                    g.dispose();

                    byte[] newData = null;
                    try {
                        ImageIO.write(image, "jpg", outputStream);
                        newData = outputStream.toByteArray();
                    } catch (IOException e) {
                        e.printStackTrace();
                    } finally {
                        outputStream.reset();
                    }

                    if (newData != null) {
                        currentBuffer.set(newData);
                        synchronized (currentBuffer) {
                            currentBuffer.notifyAll();
                        }
                    }
                }

                try {
                    long remainingTime = sleepTill - System.currentTimeMillis();
                    if (remainingTime > 0)
                        Thread.sleep(remainingTime);
                } catch (InterruptedException e) {
                    return;
                }
            }
        }

        public void registerListener() {
            listenerCount.incrementAndGet();
        }

        public void unregisterListener() {
            listenerCount.decrementAndGet();
        }

        public void waitForData() throws InterruptedException {
            synchronized (currentBuffer) {
                currentBuffer.wait();
            }
        }

        public byte[] getData() {
            return currentBuffer.get();
        }
    }

    private class HttpMultipartReplaceStream implements ChunkedInput {
        private final byte[] header;
        private boolean closed;

        public HttpMultipartReplaceStream(String boundary) {
            this.header = ("--" + boundary + "\r\nContent-Type: image/jpeg\r\n\r\n").getBytes();

            renderer.registerListener();
        }

        @Override
        public void close() throws Exception {
            if (closed)
                return;

            closed = true;
            renderer.unregisterListener();
        }

        @Override
        public boolean hasNextChunk() throws Exception {
            return !closed;
        }

        @Override
        public boolean isEndOfInput() throws Exception {
            return closed;
        }

        @Override
        public Object nextChunk() throws Exception {
            if (closed)
                return null;

            renderer.waitForData();
            byte[] body = renderer.getData();

            return ChannelBuffers.wrappedBuffer(header, body);
        }
    }

    private class HttpStreamerHandler extends SimpleChannelUpstreamHandler {
        @Override
        public void messageReceived(ChannelHandlerContext ctx, MessageEvent e) throws Exception {
            HttpRequest request = (HttpRequest) e.getMessage();
            if (request.getMethod() != GET) {
                sendError(ctx, METHOD_NOT_ALLOWED);
                return;
            } else if (!"/stream".equals(request.getUri())) {
                sendError(ctx, NOT_FOUND);
                return;
            }

            final String boundary = "thisisourmagicboundary";
            HttpResponse response = new DefaultHttpResponse(HTTP_1_1, OK);
            HttpHeaders.setHeader(response, "Connection", "close");
            HttpHeaders.setHeader(response, "Content-Type", "multipart/x-mixed-replace;boundary=" + boundary);
            HttpHeaders.setHeader(response, "Cache-control", "no-cache");
            HttpHeaders.setHeader(response, "Pragma", "no-cache");
            HttpHeaders.setHeader(response, "Expires", "Thu, 01 Dec 1994 16:00:00 GMT");

            Channel ch = e.getChannel();

            final HttpMultipartReplaceStream replaceStream = new HttpMultipartReplaceStream(boundary);
            ch.getCloseFuture().addListener(new ChannelFutureListener() {
                @Override
                public void operationComplete(ChannelFuture future) throws Exception {
                    // Stop the stream when the channel is closed
                    replaceStream.close();
                }
            });

            // Write the initial line and the headers
            ch.write(response);

            // Write the content
            ChannelFuture writeFuture = ch.write(replaceStream);

            // Close the connection when the whole content is written out
            writeFuture.addListener(ChannelFutureListener.CLOSE);
        }

        @Override
        public void exceptionCaught(ChannelHandlerContext ctx, ExceptionEvent e) throws Exception {
            Channel ch = e.getChannel();
            Throwable cause = e.getCause();
            if (cause instanceof TooLongFrameException) {
                sendError(ctx, BAD_REQUEST);
                return;
            } else if (cause instanceof ClosedChannelException) {
                ch.close();
                return;
            }

            cause.printStackTrace();
            if (ch.isConnected())
                sendError(ctx, INTERNAL_SERVER_ERROR);
        }

        private void sendError(ChannelHandlerContext ctx, HttpResponseStatus status) {
            HttpResponse response = new DefaultHttpResponse(HTTP_1_1, status);
            response.setHeader(CONTENT_TYPE, "text/plain; charset=UTF-8");
            response.setContent(ChannelBuffers.copiedBuffer("Failure: " + status.toString() + "\r\n", CharsetUtil.UTF_8));

            // Close the connection as soon as the error message is sent.
            ctx.getChannel().write(response).addListener(ChannelFutureListener.CLOSE);
        }
    }

    public Streamer(int port, Component view) {
        this.port = port;
        this.view = view;
        this.renderer = new ViewRenderer();
    }

    public void run() {
        // Configure the server.
        ServerBootstrap bootstrap = new ServerBootstrap(new NioServerSocketChannelFactory(Executors.newCachedThreadPool(), Executors.newCachedThreadPool()));

        // Set up the event pipeline factory.
        bootstrap.setPipelineFactory(new ChannelPipelineFactory() {
            @Override
            public ChannelPipeline getPipeline() throws Exception {
                // Create a default pipeline implementation.
                ChannelPipeline pipeline = Channels.pipeline();

                pipeline.addLast("decoder", new HttpRequestDecoder());
                pipeline.addLast("aggregator", new HttpChunkAggregator(65536));
                pipeline.addLast("encoder", new HttpResponseEncoder());
                pipeline.addLast("chunkedWriter", new ChunkedWriteHandler());
                pipeline.addLast("handler", new HttpStreamerHandler());

                return pipeline;
            }
        });

        // Bind and start to accept incoming connections.
        bootstrap.bind(new InetSocketAddress(port));

        // Start the renderer
        new Thread(renderer, "Image renderer").start();
    }
}