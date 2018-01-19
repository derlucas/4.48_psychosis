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
    private ImagePanel imagePanel;
    private boolean heart1;
    private boolean heart2;
    private boolean heart3;

    public ActorHeart() {
        imagePanel = new ImagePanel("/de/psychose/heart1_klein_inv.jpg", "/de/psychose/heart2_klein_inv.jpg");
        mainPanel.add(imagePanel);
        mainPanel.setBackground(Color.black);
    }

    public void update(boolean heart1, boolean heart2, boolean heart3) {
        this.heart1 = heart1;
        this.heart2 = heart2;
        this.heart3 = heart3;
        imagePanel.repaint();
    }

    public void update1(boolean heart1) {
        this.heart1 = heart1;
        imagePanel.repaint();
    }

    public void update2(boolean heart2) {
        this.heart2 = heart2;
        imagePanel.repaint();
    }

    public void update3(boolean heart3) {
        this.heart3 = heart3;
        imagePanel.repaint();
    }

    private class ImagePanel extends JPanel {
        private BufferedImage image1;
        private BufferedImage image2;

        ImagePanel(String imageA, String imageB) {
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
            g.drawImage(heart1 ? image1 : image2, 0, 0, null, null);
            g.drawImage(heart2 ? image1 : image2, 263, 0, null, null);
            g.drawImage(heart3 ? image1 : image2, 263 * 2, 0, null, null);
        }
    }
}
