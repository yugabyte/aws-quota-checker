from .quota_check import QuotaCheck, QuotaScope

import boto3
import cachetools

@cachetools.cached(cache=cachetools.TTLCache(1, 60))
def get_all_ebs_volumes(session: boto3.Session):
    return session.client('ec2').describe_volumes(
            Filters=[
                {
                    'Name': 'volume-type',
                    'Values': ['gp3'],
                }
            ]
            )['Volumes']

class SnapshotCountCheck(QuotaCheck):
    key = "ebs_snapshot_count"
    description = "EBS Snapshots per Region"
    scope = QuotaScope.REGION
    service_code = 'ebs'
    quota_code = 'L-309BACF6'

    @property
    def current(self):
        return self.count_paginated_results("ec2", "describe_snapshots", "Snapshots", {"OwnerIds": ["self"]})

class StorageSSDGP2(QuotaCheck, ):
    key = "ebs_storage_amount_gp2"
    description = "Storage for General Purpose SSD (gp2)"
    scope = QuotaScope.REGION
    service_code = 'ebs'
    quota_code = 'L-D18FCD1D'

    @property
    def current(self):
        volumes = filter(lambda vol: vol['VolumeType'] == 'gp2', get_all_ebs_volumes(self.boto_session))
        return sum(vol['Size'] for vol in volumes) / 1000

class StorageSSDGP3(QuotaCheck, ):
    key = "ebs_storage_amount_gp3"
    description = "Storage for General Purpose SSD (gp3)"
    scope = QuotaScope.REGION
    service_code = 'ebs'
    quota_code = 'L-7A658B76'

    @property
    def current(self):
        volumes = filter(lambda vol: vol['VolumeType'] == 'gp3', get_all_ebs_volumes(self.boto_session))
        return sum(vol['Size'] for vol in volumes) / 1000
