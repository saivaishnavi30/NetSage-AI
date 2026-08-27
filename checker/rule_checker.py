import ipaddress
import re


def check_duplicate_ips(devices):
    """Check whether multiple devices have the same IP address."""
    seen = {}
    problems = []

    for device in devices:
        ip = device.get("ip")

        if not ip:
            continue

        if ip in seen:
            problems.append(
                f"Duplicate IP {ip}: {seen[ip]} and {device['name']}"
            )
        else:
            seen[ip] = device["name"]

    return problems


def check_wrong_masks(devices):
    """Check whether an IP address belongs to the declared network."""
    problems = []

    for device in devices:
        ip = device.get("ip")
        mask = device.get("mask")
        network = device.get("network")

        if not ip or not mask or not network:
            continue

        try:
            actual_network = ipaddress.ip_network(
                f"{ip}/{mask}",
                strict=False
            )

            expected_network = ipaddress.ip_network(
                network,
                strict=False
            )

            if actual_network.network_address != expected_network.network_address:
                problems.append(
                    f"Wrong mask/network for {device['name']}: "
                    f"{ip}/{mask} belongs to {actual_network}, "
                    f"expected {expected_network}"
                )

        except ValueError:
            problems.append(
                f"Invalid IP/mask configuration on {device['name']}"
            )

    return problems


def check_gateway_mismatch(devices):
    """Check whether the gateway belongs to the same subnet as the device."""
    problems = []

    for device in devices:
        ip = device.get("ip")
        mask = device.get("mask")
        gateway = device.get("gateway")

        if not ip or not mask or not gateway:
            continue

        try:
            network = ipaddress.ip_network(
                f"{ip}/{mask}",
                strict=False
            )

            gateway_ip = ipaddress.ip_address(gateway)

            if gateway_ip not in network:
                problems.append(
                    f"Gateway mismatch for {device['name']}: "
                    f"{gateway} is outside {network}"
                )

        except ValueError:
            problems.append(
                f"Invalid gateway configuration on {device['name']}"
            )

    return problems


def check_interfaces(interfaces):
    """Check whether any required interface is administratively down."""
    problems = []

    for interface in interfaces:
        if interface.get("required", True) and interface.get("status") != "up":
            problems.append(
                f"Interface down: {interface['name']}"
            )

    return problems


def check_vlans(required_vlans, configured_vlans):
    """Check whether required VLANs exist."""
    problems = []

    configured = set(configured_vlans)

    for vlan in required_vlans:
        if vlan not in configured:
            problems.append(
                f"Missing VLAN: {vlan}"
            )

    return problems


def check_routes(required_routes, routing_table):
    """Check whether required destination networks have routes."""
    problems = []

    configured_routes = set(routing_table)

    for route in required_routes:
        if route not in configured_routes:
            problems.append(
                f"Missing route: {route}"
            )

    return problems


def run_all_checks(configuration):
    """Run all deterministic network checks."""

    results = {
        "duplicate_ips": check_duplicate_ips(
            configuration.get("devices", [])
        ),

        "wrong_masks": check_wrong_masks(
            configuration.get("devices", [])
        ),

        "gateway_mismatches": check_gateway_mismatch(
            configuration.get("devices", [])
        ),

        "interfaces_down": check_interfaces(
            configuration.get("interfaces", [])
        ),

        "missing_vlans": check_vlans(
            configuration.get("required_vlans", []),
            configuration.get("configured_vlans", [])
        ),

        "missing_routes": check_routes(
            configuration.get("required_routes", []),
            configuration.get("routing_table", [])
        )
    }

    total_problems = sum(
        len(items)
        for items in results.values()
    )

    results["total_problems"] = total_problems

    return results


if __name__ == "__main__":

    # Demonstration configuration
    sample_configuration = {

        "devices": [
            {
                "name": "PC1",
                "ip": "192.168.10.10",
                "mask": "24",
                "gateway": "192.168.20.1",
                "network": "192.168.10.0/24"
            },
            {
                "name": "PC2",
                "ip": "192.168.10.10",
                "mask": "24",
                "gateway": "192.168.10.1",
                "network": "192.168.10.0/24"
            }
        ],

        "interfaces": [
            {
                "name": "R1-G0/0",
                "status": "up",
                "required": True
            },
            {
                "name": "R1-G0/1",
                "status": "down",
                "required": True
            }
        ],

        "required_vlans": [
            "10",
            "20",
            "30"
        ],

        "configured_vlans": [
            "10",
            "20"
        ],

        "required_routes": [
            "192.168.20.0/24",
            "192.168.30.0/24"
        ],

        "routing_table": [
            "192.168.20.0/24"
        ]
    }

    print("=" * 60)
    print("NetSage AI - Deterministic Rule Checker")
    print("=" * 60)

    results = run_all_checks(sample_configuration)

    for category, problems in results.items():

        if category == "total_problems":
            continue

        print(f"\n{category.upper()}:")

        if problems:
            for problem in problems:
                print(f"  [!] {problem}")
        else:
            print("  [OK] No problems detected")

    print("\n" + "=" * 60)
    print(
        f"TOTAL PROBLEMS DETECTED: "
        f"{results['total_problems']}"
    )
    print("=" * 60)
