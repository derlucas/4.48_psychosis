package de.psychose;

import javax.swing.*;
import java.awt.event.ActionEvent;

/**
 * @author: lucas
 * @date: 14.04.14 21:43
 */
public class MainForm extends JFrame {
    private JPanel mainPanel;
    private ActorHeart heart;
    private ActorDisplay actor1;
    private ActorDisplay actor2;
    private ActorDisplay actor3;
    private JLabel breath;

    public MainForm(final ActorData[] actorDatas) {
        super("HD Main");
        setContentPane(mainPanel);
        setResizable(false);
        setDefaultCloseOperation(WindowConstants.EXIT_ON_CLOSE);
        setUndecorated(true);

        actor1.init(actorDatas[0], false);
        actor2.init(actorDatas[1], false);
        actor3.init(actorDatas[2], false);
        heart.setActorDatas(actorDatas);

        // this is now our main timer to update all and everything gui related
        final Timer timer = new Timer(50, new AbstractAction() {
            @Override
            public void actionPerformed(ActionEvent e) {
                // update the breath display
                breath.setText(String.valueOf(actorDatas[0].getAirflow()));

                actor1.update();
                actor2.update();
                actor3.update();
                heart.update();
            }
        });
        timer.start();

        pack();
        setVisible(true);
    }





}
