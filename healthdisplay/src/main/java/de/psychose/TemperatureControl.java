package de.psychose;

import javax.swing.*;
import javax.swing.event.ChangeEvent;
import javax.swing.event.ChangeListener;
import java.util.Observable;

/**
 * @author: lucas
 * @date: 20.11.14 23:11
 */
public class TemperatureControl extends Observable {
    private static final double MIN_OFFSET = -20;
    private static final double MAX_OFFSET = 20;
    private static final double INCREMENT = 0.1;
    private JSpinner spinner1;
    private JPanel mainPanel;

    public TemperatureControl() {
        spinner1.setModel(new SpinnerNumberModel(0, MIN_OFFSET, MAX_OFFSET, INCREMENT));

        ChangeListener changeListener = new ChangeListener() {
            @Override
            public void stateChanged(ChangeEvent e) {
                setChanged();
                notifyObservers(spinner1.getValue());
            }
        };

        spinner1.addChangeListener(changeListener);
    }
}
