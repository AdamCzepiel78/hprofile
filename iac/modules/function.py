import pulumi
import pulumi_aws as aws
import json
from modules.vpc import vpc_id, private_subnets
from modules.rds import rds_endpoint,rds_security_group


# configuration 
config = pulumi.Config('rds')
db_username = config.get("db_username") or "admin"
db_password = config.get("dp_password") or "Pa55w.rd"
db_name = config.get("db_name") or "accounts"
rds_host = rds_endpoint.split(":")[0]
rds_port = rds_endpoint.split(":")[1]


# Create IAM role for Lambda function
lambda_role = aws.iam.Role("lambda-role",
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Action": "sts:AssumeRole",
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            }
        }]
    })
)

# Attach policies for RDS access to the Lambda role
lambda_role_policy = aws.iam.RolePolicy("lambda-rds-policy",
    role=lambda_role.id,
    policy=json.dumps({
    "Version": "2012-10-17",
    "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "rds:DescribeDBInstances",
                    "rds:DescribeDBClusters",
                    "ec2:DescribeInstances",
                    "ec2:CreateNetworkInterface",
                    "ec2:AttachNetworkInterface",
                    "ec2:DescribeNetworkInterfaces",
                    "autoscaling:CompleteLifecycleAction",
                    "ec2:DeleteNetworkInterface"
                ],
                "Resource": "*"
            }
        ]
    })
)

# Grant the Lambda function the necessary permissions to access the RDS instance
lambda_security_group = aws.ec2.SecurityGroup("lambda-sg",
    description="Lambda Security Group",
    vpc_id=vpc_id,
    egress=[aws.ec2.SecurityGroupEgressArgs(
        cidr_blocks=["0.0.0.0/0"],
        protocol="-1",
        from_port=0,
        to_port=0
    )],
    ingress=[aws.ec2.SecurityGroupIngressArgs(
        protocol="tcp",
        from_port=3306,
        to_port=3306,
        security_groups=[rds_security_group.id]
    )]
)

# Attach the Lambda security group
lambda_function_security_group_attachment = aws.ec2.SecurityGroupRule("lambda-to-rds-ingress",
    type="ingress",
    security_group_id=rds_security_group.id,
    source_security_group_id=lambda_security_group.id,
    from_port=3306,
    to_port=3306,
    protocol="tcp"
)

# Lambda function deployment
lambda_function = aws.lambda_.Function("rds-execute-schema",
    role=lambda_role.arn,
    handler="rds.lambda_handler",   # Name of the Lambda function
    runtime="python3.12",                        # Lambda runtime
    code=pulumi.FileArchive("functions/sql/rds.zip"),  # Path to your zip file
    vpc_config=aws.lambda_.FunctionVpcConfigArgs(
        subnet_ids=[subnet.id for subnet in private_subnets],  # Use all private subnets
        security_group_ids=[lambda_security_group.id]
    ),
    environment={
        "variables": {
            "RDS_HOST": rds_host,
            "RDS_PORT": int(rds_port),
            "DB_USER": db_username,
            "DB_PASSWORD": db_password,
            "DB_NAME": db_name,
            "SQL_FILEPATH": "db_backup.sql"
        }
    }
)