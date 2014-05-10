package de.psychose;

import javax.swing.*;
import java.awt.event.ActionEvent;
import java.awt.event.ItemEvent;
import java.awt.event.ItemListener;
import java.util.Observable;
import java.util.Random;

/**
 * @author: lucas
 * @date: 03.05.14 10:10
 */
public class PulseControl extends Observable {
    private final int PULSE_WOBBLE_WIDTH = 10;
    private JCheckBox enableCheckBox;
    private JSpinner spinner1;
    private JPanel pulsePanel;
    private Timer timer;
    private Random random = new Random();
    private int heartbeat = 0;


    public PulseControl() {
        enableCheckBox.setFocusable(false);
        spinner1.setFocusable(false);
        spinner1.setValue(110);

        timer = new Timer(100, new AbstractAction() {
            @Override
            public void actionPerformed(ActionEvent e) {
                heartbeat = (heartbeat+1) % 2;

                final int pulseWobbleCenter = (int)spinner1.getValue();
                int pulse = pulseWobbleCenter - PULSE_WOBBLE_WIDTH / 2 + random.nextInt(PULSE_WOBBLE_WIDTH);

                if(pulse < 60) pulse = 60;
                if(pulse > 180) pulse = 180;

                final PulseData data = new PulseData(heartbeat, pulse, 95 + random.nextInt(4));
                setChanged();
                notifyObservers(data);

                final int delay = 60000 / pulse;
                timer.setDelay(delay);
            }
        });

        timer.setRepeats(true);

        enableCheckBox.addItemListener(new ItemListener() {
            @Override
            public void itemStateChanged(ItemEvent e) {
                System.out.println("item state changed");
                JCheckBox checkBox = (JCheckBox)e.getSource();
                if(checkBox.isSelected()) {
                    if(!timer.isRunning()) {
                        System.out.println("starting pulsecontrol " + this);
                        timer.start();
                    }
                } else {
                    if(timer.isRunning()) {
                        System.out.println("stopping pulsecontrol " + this);
                        timer.stop();
                    }
                }

            }
        });
    }

    public void hide() {
        this.pulsePanel.setVisible(false);
    }

}
