import pulumi
import pulumi_aws as aws

# Configuration
config = pulumi.Config()
vpc_cidr = config.get("vpc_cidr") or "10.0.0.0/16"
public_subnet_cidr = config.get("public_subnet_cidr") or "10.0.1.0/24"
private_subnet_cidrs = config.get("private_subnet_cidrs") or ["10.0.2.0/24", "10.0.3.0/24", "10.0.4.0/24"]

# Create a VPC
vpc = aws.ec2.Vpc("gh-vpc",
    cidr_block=vpc_cidr,
    enable_dns_support=True,
    enable_dns_hostnames=True,
    tags={"Name": "ghActionsVPC"}
)

# Create an Internet Gateway
igw = aws.ec2.InternetGateway("gh-igw",
    vpc_id=vpc.id,
    tags={"Name": "ghActionsIGW"}
)

# Create a public route table
public_route_table = aws.ec2.RouteTable("publicRouteTable",
    vpc_id=vpc.id,
    routes=[
        aws.ec2.RouteTableRouteArgs(
            cidr_block="0.0.0.0/0",
            gateway_id=igw.id,
        )
    ],
    tags={"Name": "ghActionsPublicRouteTable"}
)

# Create a public subnet
public_subnet = aws.ec2.Subnet("publicSubnet",
    vpc_id=vpc.id,
    cidr_block=public_subnet_cidr,
    map_public_ip_on_launch=True,
    availability_zone="us-east-1a",
    tags={"Name": "ghActionsPublicSubnet"}
)

# Associate the public subnet with the public route table
public_route_table_association = aws.ec2.RouteTableAssociation("publicRouteTableAssociation",
    subnet_id=public_subnet.id,
    route_table_id=public_route_table.id
)

# Create private subnets
private_subnets = []
for i, cidr in enumerate(private_subnet_cidrs):
    private_subnet = aws.ec2.Subnet(f"privateSubnet-{i}",
        vpc_id=vpc.id,
        cidr_block=cidr,
        availability_zone=f"us-east-1{chr(98 + i)}",
        tags={"Name": f"ghActionsPrivateSubnet-{i}"}
    )
    private_subnets.append(private_subnet)

db_subnet_group = aws.rds.SubnetGroup("db-subnet-group",
    subnet_ids=[public_subnet.id] + [subnet.id for subnet in private_subnets],
    tags={"name": "my-db-subnet-group"}
)

# Output VPC and subnet information
pulumi.export("vpc_id", vpc.id)
pulumi.export("public_subnet_id", public_subnet.id)
pulumi.export("private_subnet_ids", [subnet.id for subnet in private_subnets])
pulumi.export("db_subnet_group_name", db_subnet_group.name)