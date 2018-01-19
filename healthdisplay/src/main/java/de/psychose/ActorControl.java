package de.psychose;

import javax.swing.*;
import java.util.Random;

/**
 * @author: lucas
 * @date: 03.05.14 10:10
 */
public class ActorControl {

    private final int PULSE_MIN = 60;
    private final int PULSE_MAX = 220;
    private final double TEMP_DEF = 36.7;
    private final double TEMP_MIN = 36.3;
    private final double TEMP_MAX = 37.5;

    private final ControlForm controlForm;

    private JSpinner spinnerPulse;
    private JPanel mainPanel;
    private JSpinner spinnerTemp;
    private JCheckBox chkSimEnable;
    private JButton btnBreath;
    private final Random random = new Random();
    private boolean heartbeat = false;
    private final String actor;

    public ActorControl(ControlForm controlForm, String actor) {
        this.controlForm = controlForm;
        this.actor = actor;
        spinnerPulse.setValue(110);

//        timer = new Timer(500, new AbstractAction() {
//            @Override
//            public void actionPerformed(ActionEvent e) {
//                heartbeat = !heartbeat;
//
//                int pulse = (int) spinnerPulse.getValue() - PULSE_WOBBLE_WIDTH / 2 + random.nextInt(PULSE_WOBBLE_WIDTH);
//
//                if (pulse < 60) pulse = 60;
//                if (pulse > 230) pulse = 230;
//
//                setChanged();
//                notifyObservers(new PulseData(heartbeat, pulse, 95 + random.nextInt(4)));
//
//
//                timer.setDelay(60000 / pulse);
//            }
//        });

//        chkSimEnable.addItemListener(e -> {
//            if (chkSimEnable.isSelected() && !timer.isRunning()) {
//                timer.start();
//            } else if (timer.isRunning()) {
//                timer.stop();
//            }
//        });


        spinnerTemp.setModel(new SpinnerNumberModel(TEMP_DEF, TEMP_MIN, TEMP_MAX, 0.1));
        spinnerPulse.setModel(new SpinnerNumberModel(110, PULSE_MIN, PULSE_MAX, 1));

        chkSimEnable.addActionListener(actionEvent -> postEvent());
        spinnerTemp.addChangeListener(changeEvent -> postEvent());
        spinnerPulse.addChangeListener(changeEvent -> postEvent());

        spinnerTemp.addMouseWheelListener(mouseWheelEvent -> {
            SpinnerNumberModel model = (SpinnerNumberModel) spinnerTemp.getModel();
            double value = (double) spinnerTemp.getValue();
            if (mouseWheelEvent.getWheelRotation() > 0) {
                value = value - (double) model.getStepSize();
            } else {
                value = value + (double) model.getStepSize();
            }

            if (value < TEMP_MIN) value = TEMP_MIN;
            if (value > TEMP_MAX) value = TEMP_MAX;
            spinnerTemp.setValue(value);
        });

        spinnerPulse.addMouseWheelListener(mouseWheelEvent -> {
            SpinnerNumberModel model = (SpinnerNumberModel) spinnerPulse.getModel();
            int value = (int) spinnerPulse.getValue();
            if (mouseWheelEvent.getWheelRotation() > 0) {
                value = value - (int) model.getStepSize();
            } else {
                value = value + (int) model.getStepSize();
            }
            if (value < PULSE_MIN) value = PULSE_MIN;
            if (value > PULSE_MAX) value = PULSE_MAX;
            spinnerPulse.setValue(value);
        });

    }

    private void postEvent() {
        ActorControlChangeEvent event = new ActorControlChangeEvent(actor);
        event.setSimulationEnabled(chkSimEnable.isSelected());
        event.setAirflow(0);
        event.setPulse((int) spinnerPulse.getValue());
        event.setTemperature((double) spinnerTemp.getValue());
        controlForm.actorControlChanges(event);
    }


}
