#!/usr/bin/env python3

import boto3
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description="Manage AZs for an Auto Scaling Group")
    parser.add_argument('--asg-name', required=True, help='Name of the Auto Scaling Group')
    parser.add_argument('--az-list', required=True, help='Comma-separated list of AZs')
    parser.add_argument('--action', required=True, choices=['attach', 'detach'], help='Action to perform')
    args = parser.parse_args()

    az_list = [az.strip() for az in args.az_list.split(',') if az.strip()]
    if not az_list:
        print("No valid AZs provided")
        sys.exit(1)

    client = boto3.client('autoscaling')
    
    # Get current ASG configuration
    response = client.describe_auto_scaling_groups(AutoScalingGroupNames=[args.asg_name])
    if not response['AutoScalingGroups']:
        print(f"ASG '{args.asg_name}' not found")
        sys.exit(1)

    asg = response['AutoScalingGroups'][0]
    current_azs = set(asg['AvailabilityZones'])
    current_subnets = set(asg.get('VPCZoneIdentifier', '').split(','))

    # Map subnets to AZs
    ec2_client = boto3.client('ec2')
    subnet_info = ec2_client.describe_subnets(SubnetIds=list(current_subnets))
    subnet_az_map = {s['AvailabilityZone']: s['SubnetId'] for s in subnet_info['Subnets']}

    # Validate AZs exist in ASG subnets
    invalid_azs = [az for az in az_list if az not in subnet_az_map]
    if invalid_azs:
        print(f"Error: The following AZs do not exist in ASG subnets: {invalid_azs}")
        sys.exit(1)

    if args.action == 'detach':
        new_azs = current_azs - set(az_list)
        if not new_azs:
            print("Cannot remove all AZs from ASG")
            sys.exit(1)
        print(f"Detaching AZs {az_list} from ASG {args.asg_name}")
    elif args.action == 'attach':
        new_azs = current_azs.union(az_list)
        print(f"Attaching AZs {az_list} to ASG {args.asg_name}")

    # Update ASG
    client.update_auto_scaling_group(
        AutoScalingGroupName=args.asg_name,
        AvailabilityZones=list(new_azs)
    )
    print(f"Updated ASG '{args.asg_name}' with AZs: {list(new_azs)}")

if __name__ == "__main__":
    main()