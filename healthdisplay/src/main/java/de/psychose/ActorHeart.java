package de.psychose;

import javax.imageio.ImageIO;
import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.image.BufferedImage;
import java.io.IOException;

/**
 * @author: lucas
 * @date: 15.11.14 21:36
 */
public class ActorHeart {
    private JPanel heartPanel;
    private ActorData actorData1;
    private ActorData actorData2;
    private ActorData actorData3;
    private ImagePanel imagePanel;
    private Timer timer;

    public ActorHeart() {
        imagePanel = new ImagePanel("/de/psychose/heart1_klein_inv.jpg", "/de/psychose/heart2_klein_inv.jpg");
        heartPanel.add(imagePanel);

        timer = new Timer(100, new AbstractAction() {
            @Override
            public void actionPerformed(ActionEvent e) {
                if(actorData1 != null && actorData2 != null && actorData3 != null) {
                    imagePanel.repaint();
                }
            }
        });
        timer.setRepeats(true);
        timer.start();
    }

    public void setActorData(final ActorData actorData1, final ActorData actorData2, final ActorData actorData3) {
        this.actorData1 = actorData1;
        this.actorData2 = actorData2;
        this.actorData3 = actorData3;
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
            if(actorData1 != null && actorData2 != null && actorData3 != null) {
                g.drawImage(ActorHeart.this.actorData1.getTommyHeartbeat() ? image1 : image2, 0, 0, null, null);
                g.drawImage(ActorHeart.this.actorData2.getTommyHeartbeat() ? image1 : image2, 263, 0, null, null);
                g.drawImage(ActorHeart.this.actorData3.getTommyHeartbeat() ? image1 : image2, 526, 0, null, null);
            }
        }
    }
}
