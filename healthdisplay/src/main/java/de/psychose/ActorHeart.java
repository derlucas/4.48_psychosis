package de.psychose;

import javax.imageio.ImageIO;
import javax.swing.*;
import java.awt.*;
import java.awt.image.BufferedImage;
import java.io.IOException;

/**
 * @author: lucas
 * @date: 15.11.14 21:36
 */
public class ActorHeart {
    private JPanel mainPanel;
    private ActorData[] actorDatas;
    private ImagePanel imagePanel;

    public ActorHeart() {
        imagePanel = new ImagePanel("/de/psychose/heart1_klein_inv.jpg", "/de/psychose/heart2_klein_inv.jpg");
        mainPanel.add(imagePanel);
        mainPanel.setBackground(Main.backgroundColor);
    }

    public void update() {
        imagePanel.repaint();
    }

    public void setActorDatas(final ActorData[] actorDatas) {
        this.actorDatas = actorDatas;
    }

    private class ImagePanel extends JPanel {
        private BufferedImage image1;
        private BufferedImage image2;

        public ImagePanel(String imageA, String imageB) {
            try {
                image1 = ImageIO.read(getClass().getResourceAsStream(imageA));
                image2 = ImageIO.read(getClass().getResourceAsStream(imageB));
            } catch (IOException e) {
                e.printStackTrace();
            }
        }

        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);

            if (actorDatas != null) {
                for (int i = 0; i < actorDatas.length; i++) {
                    if (actorDatas[i] != null) {
                        g.drawImage(actorDatas[i].getTommyHeartbeat() ? image1 : image2, 263 * i, 0, null, null);
                    }
                }
            }
        }
    }
}
