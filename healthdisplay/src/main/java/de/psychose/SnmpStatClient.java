package de.psychose;

import org.snmp4j.CommunityTarget;
import org.snmp4j.Snmp;
import org.snmp4j.TransportMapping;
import org.snmp4j.mp.SnmpConstants;
import org.snmp4j.smi.OID;
import org.snmp4j.smi.OctetString;
import org.snmp4j.smi.UdpAddress;
import org.snmp4j.smi.VariableBinding;
import org.snmp4j.transport.DefaultUdpTransportMapping;
import org.snmp4j.util.DefaultPDUFactory;
import org.snmp4j.util.TreeEvent;
import org.snmp4j.util.TreeUtils;

import java.io.IOException;
import java.util.HashMap;
import java.util.List;

/**
 * @author: lucas
 * @date: 18.04.14 12:10
 */
public class SnmpStatClient {
    public static final String OID_COUNTER = "1.3.6.1.2.1.2.2.1.10";
    private HashMap<Integer, Long> lastPorts = new HashMap<>();
    private HashMap<Integer, Long> sumPorts = new HashMap<>();
    private Snmp snmp;
    private CommunityTarget communityTarget;

    private CommunityTarget getCommunityTarget(String host) {
        CommunityTarget communityTarget = new CommunityTarget();
        communityTarget.setCommunity(new OctetString("public"));
        communityTarget.setVersion(SnmpConstants.version2c);
        communityTarget.setAddress(new UdpAddress(host));
        communityTarget.setTimeout(100);
        return communityTarget;
    }

    public SnmpStatClient(String host) {
        try {
            final TransportMapping transportMapping = new DefaultUdpTransportMapping();
            transportMapping.listen();

            this.communityTarget = getCommunityTarget(host);
            this.snmp = new Snmp(transportMapping);

        } catch (IOException e) {
            System.out.println("error: cannot get traffic from snmp target");
        }
    }

    public long getTrafficSum() {

        if (snmp == null || this.communityTarget == null) {
            System.out.println("snmp error");
            return 0;
        }

        long sum = 0;

        try {

            final TreeUtils treeUtils = new TreeUtils(snmp, new DefaultPDUFactory());
            final List<TreeEvent> treeEventList = treeUtils.getSubtree(this.communityTarget, new OID(OID_COUNTER));

            for (TreeEvent treeEvent : treeEventList) {
                if (treeEvent.getStatus() == TreeEvent.STATUS_OK) {
                    for (VariableBinding binding : treeEvent.getVariableBindings()) {
                        int oid = binding.getOid().last();
                        long value = binding.getVariable().toLong() / 1024;     // convert bytes down to kilobytes
                        long lastValue = 0;
                        if (lastPorts.containsKey(oid)) lastValue = lastPorts.get(oid);
                        long diff = value - lastValue;

                        if (diff > 0) {
                            sumPorts.put(oid, lastValue + diff);
                        }
                    }
                }
            }
        } catch (IllegalArgumentException e) {
            System.out.println("error: could not resolve address from snmp target");
        }

        for (long port : sumPorts.values()) {
            sum += port;
        }

        return sum;
    }

}
