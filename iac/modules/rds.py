import pulumi
import pulumi_aws as aws
from modules.vpc import private_subnets,vpc_id

# Configuration
config = pulumi.Config('rds')
db_name = config.get("db_name") or "accounts"
db_username = config.get("db_username") or "admin"
db_password = config.get("dp_password") or "Pa55w.rd"
db_instance_class = config.get("db_instance_class") or "db.t3.micro"
db_allocated_storage = config.get_int("db_allocated_storage") or 20


# Create a security group for the RDS instance
rds_security_group = aws.ec2.SecurityGroup("gh-actions-rds-sg",
    description="Allow MySQL access",
    vpc_id=vpc_id,
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=3306,
            to_port=3306,
            cidr_blocks=["10.0.0.0/16"],  # Allow from all (replace with restricted CIDR range for security)
        ),
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],
        ),
    ]
)
# create subnet group 
rds_subnet_group = aws.rds.SubnetGroup("gh-rds-subnet-group",
                                        subnet_ids=[subnet.id for subnet in private_subnets],
                                        tags={"Name": "gh-rds-subnet-group"}
                                        )

# Create an RDS MySQL instance
rds_instance = aws.rds.Instance("gh-actions-instance",
    engine="mysql",
    instance_class=db_instance_class,
    allocated_storage=db_allocated_storage,
    db_name=db_name,
    username=db_username,
    password=db_password,
    publicly_accessible=True,
    backup_retention_period=7,  # Retain backups for 7 days
    skip_final_snapshot=True,  # Optional: skip final snapshot on delete
    vpc_security_group_ids=[rds_security_group.id],
    db_subnet_group_name=rds_subnet_group.name,
    tags={
        "Environment": "Dev",
        "Name": "MyRDSInstance"
    }
)
# env vars for lambda job 
rds_endpoint =  rds_instance.endpoint

# Export the RDS instance endpoint
pulumi.export("rds_endpoint", rds_instance.endpoint)
pulumi.export("rds_username", db_username)
pulumi.export("rds_password", db_password)
