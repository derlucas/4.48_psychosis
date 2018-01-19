package de.psychose;

import javax.swing.*;
import java.awt.*;

/**
 * @author: lucas
 * @date: 14.04.14 21:43
 */
public class PresenterForm extends JFrame implements UpdateInterface {
    private JPanel mainPanel;
    private ActorHeart heart;
    private ActorDisplay actor1;
    private ActorDisplay actor2;
    private ActorDisplay actor3;
    private JLabel breath;

    public PresenterForm() {
        super("HD Main");
        setContentPane(mainPanel);
        setResizable(false);
        setDefaultCloseOperation(WindowConstants.EXIT_ON_CLOSE);
        setUndecorated(true);
        mainPanel.setBackground(Color.black);


        // this is now our main timer to update all and everything gui related
//        final Timer timer = new Timer(40, new AbstractAction() {
//            @Override
//            public void actionPerformed(ActionEvent e) {
//                update();
//            }
//        });
//        timer.start();

        pack();
        setVisible(true);

    }


    @Override
    public void update(ActorData[] actorDatas) {
        actor1.update(actorDatas[0]);
        actor2.update(actorDatas[1]);
        actor3.update(actorDatas[2]);
        breath.setText(String.valueOf(actorDatas[0].getAirflow()));
        heart.update1(actorDatas[0].isTommyHeartbeat());
        heart.update2(actorDatas[1].isTommyHeartbeat());
        heart.update3(actorDatas[2].isTommyHeartbeat());
    }
}
