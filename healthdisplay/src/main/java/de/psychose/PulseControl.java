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
    private JSpinner spinner;
    private JPanel mainPanel;
    private final Timer timer;
    private final Random random = new Random();
    private boolean heartbeat = false;

    public PulseControl() {
        spinner.setValue(110);

        timer = new Timer(500, new AbstractAction() {
            @Override
            public void actionPerformed(ActionEvent e) {
                heartbeat = !heartbeat;

                int pulse = (int) spinner.getValue() - PULSE_WOBBLE_WIDTH / 2 + random.nextInt(PULSE_WOBBLE_WIDTH);

                if(pulse < 60) pulse = 60;
                if(pulse > 230) pulse = 230;

                setChanged();
                notifyObservers(new PulseData(heartbeat, pulse, 95 + random.nextInt(4)));

                timer.setDelay(60000 / pulse);
            }
        });

        enableCheckBox.addItemListener(new ItemListener() {
            @Override
            public void itemStateChanged(ItemEvent e) {
                if (enableCheckBox.isSelected() && !timer.isRunning()) {
                    timer.start();
                } else if (timer.isRunning()) {
                    timer.stop();
                }
            }
        });
    }
}
