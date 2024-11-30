import pulumi
import pulumi_aws as aws

# Create an ECR repository
repository = aws.ecr.Repository("gh-actions-registry",
    lifecycle_policy={
        "rules": [{
            "rulePriority": 10,
            "description": "Expire untagged images",
            "selection": {
                "tagStatus": "UNTAGGED",
                "countType": "imageCountMoreThan",
                "countNumber": 10
            },
            "action": {
                "type": "expire"
            }
        }]
    }
)



# Output the repository URL
pulumi.export("repository_url", repository.repository_url)

