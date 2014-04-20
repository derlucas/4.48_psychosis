package de.psychose;

import javax.swing.*;

/**
 * @author: lucas
 * @date: 18.04.14 02:19
 */
public class StatsDisplay {
    private JLabel lblCaption;
    private JLabel lblMessageCount;
    private JLabel lblMessagesPerSec;
    private JPanel statPanel;

    public void setMessageCount(String count) {
        lblMessageCount.setText(count);
    }

    public void setMessagesPerSec(String messagesPerSec) {
        lblMessagesPerSec.setText(messagesPerSec);
    }

}
