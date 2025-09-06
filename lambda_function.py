#!/usr/bin/env python3

import boto3
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description="Manage Subnets for an Auto Scaling Group")
    parser.add_argument('--asg-name', required=True, help='Name of the Auto Scaling Group')
    parser.add_argument('--subnet-list', required=True, help='Comma-separated list of AZ|SubnetID')
    parser.add_argument('--action', required=True, choices=['attach', 'detach'], help='Action to perform')

    args = parser.parse_args()

    # Extract subnet IDs from input
    subnet_entries = [s.strip() for s in args.subnet_list.split(',') if s.strip()]
    subnet_ids = [entry.split('|')[1].strip() for entry in subnet_entries]

    if not subnet_ids:
        print("No valid subnets provided")
        sys.exit(1)

    client = boto3.client('autoscaling')

    # Get current ASG configuration
    response = client.describe_auto_scaling_groups(AutoScalingGroupNames=[args.asg_name])
    if not response['AutoScalingGroups']:
        print(f"ASG '{args.asg_name}' not found")
        sys.exit(1)

    asg = response['AutoScalingGroups'][0]
    current_subnets = set(asg.get('VPCZoneIdentifier', '').split(',')) if asg.get('VPCZoneIdentifier') else set()

    if args.action == 'detach':
        new_subnets = current_subnets - set(subnet_ids)
        if not new_subnets:
            print("Cannot remove all subnets from ASG")
            sys.exit(1)
        print(f"Detaching subnets {subnet_ids} from ASG {args.asg_name}")
    elif args.action == 'attach':
        new_subnets = current_subnets.union(subnet_ids)
        print(f"Attaching subnets {subnet_ids} to ASG {args.asg_name}")

    # Update ASG
    client.update_auto_scaling_group(
        AutoScalingGroupName=args.asg_name,
        VPCZoneIdentifier=','.join(new_subnets)
    )

    print(f"Updated ASG '{args.asg_name}' with subnets: {list(new_subnets)}")

if __name__ == "__main__":
    main()
