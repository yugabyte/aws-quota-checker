from .quota_check import QuotaCheck, QuotaScope

import boto3
import cachetools


@cachetools.cached(cache=cachetools.TTLCache(1, 60))
def get_all_running_ec2_instances(session: boto3.Session):
    return [instance for reservations in session.client('ec2').describe_instances(
            Filters=[
                {
                    'Name': 'instance-state-name',
                    'Values': ['running']
                }
            ]
            )['Reservations'] for instance in reservations['Instances']]


@cachetools.cached(cache=cachetools.TTLCache(1, 60))
def get_all_spot_requests(session: boto3.Session):
    return session.client('ec2').describe_spot_instance_requests()[
        'SpotInstanceRequests']

class OnDemandStandardInstanceVCpuCheck(QuotaCheck):
    """
    Checks the total vCPUs for all running On-Demand EC2 instances in the
    Standard family (A, C, D, H, I, M, R, T, Z) against the service quota.
    """
    # The key is updated to reflect that it checks vCPUs, not a simple count.
    key = "ec2_on_demand_standard_vcpu"

    # The description is also updated for clarity.
    description = "Running On-Demand Standard (A, C, D, H, I, M, R, T, Z) vCPUs"

    scope = QuotaScope.ACCOUNT
    service_code = "ec2"

    # The QuotaCode vCPU limits.
    quota_code = "L-1216C47A"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Cache to store the vCPU map to avoid repeated API calls
        self._instance_vcpu_map = {}

    def _get_instance_vcpu_map(self):
        """
        Dynamically retrieves vCPU counts for instance types and caches them.
        """
        if self._instance_vcpu_map:
            return self._instance_vcpu_map

        ec2_client = self.boto_session.client("ec2")

        # describe_instance_type_offerings lists instance types available in a region.
        instance_types_response = ec2_client.describe_instance_type_offerings(
            LocationType="region",
            Filters=[
                {
                    'Name': 'instance-type',
                    'Values': ['a*', 'c*', 'd*', 'h*', 'i*', 'm*', 'r*', 't*', 'z*']
                }
            ]
        )

        # Handle pagination if the list is very long
        all_instance_types_offered = [item['InstanceType'] for item in instance_types_response.get('InstanceTypeOfferings', [])]

        # --- CRITICAL FIX: Chunk the list of instance types to avoid API limit ---
        # The API parameter 'InstanceTypes' cannot exceed 100 items.

        chunk_size = 100
        instance_details_response = {'InstanceTypes': []}

        for i in range(0, len(all_instance_types_offered), chunk_size):
            chunk = all_instance_types_offered[i:i + chunk_size]
            response = ec2_client.describe_instance_types(
                InstanceTypes=chunk
            )
            instance_details_response['InstanceTypes'].extend(response['InstanceTypes'])
        # --- END OF CRITICAL FIX ---

        # Populate the vCPU map from the API response
        for detail in instance_details_response.get('InstanceTypes', []):
            self._instance_vcpu_map[detail['InstanceType']] = detail['VCpuInfo']['DefaultVCpus']

        return self._instance_vcpu_map

    @property
    def current(self):
        """
        Calculates the total number of vCPUs for all running On-Demand instances
        in the Standard family.
        """
        ec2_resource = self.boto_session.resource("ec2")
        instances = ec2_resource.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
        running_instances_list = [{"InstanceType": i.instance_type} for i in instances]

        instance_vcpu_map = self._get_instance_vcpu_map()

        # Filter for instances in the specified families.
        standard_instances = filter(
            lambda inst: inst['InstanceType'][0] in ['a', 'c', 'd', 'h', 'i', 'm', 'r', 't', 'z'],
            running_instances_list
        )

        total_vcpus = 0
        for instance in standard_instances:
            instance_type = instance['InstanceType']
            # Lookup the vCPU count for each instance.
            # Use .get() with a default of 0 to gracefully handle unknown types.
            vcpus = instance_vcpu_map.get(instance_type, 0)
            if vcpus > 0:
                # This line is for debugging, you can remove it in production
                # print(f"Found running instance of type '{instance_type}' with {vcpus} vCPUs.")
                pass
            total_vcpus += vcpus

        return total_vcpus


class OnDemandFInstanceCountCheck(QuotaCheck):
    key = "ec2_on_demand_f_count"
    description = "Running On-Demand F EC2 instances"
    scope = QuotaScope.ACCOUNT
    service_code = "ec2"
    quota_code = "L-74FC7D96"

    @property
    def current(self):
        instances = get_all_running_ec2_instances(self.boto_session)

        return len(list(filter(lambda inst: inst['InstanceType'][0] in ['f'], instances)))


class OnDemandGInstanceCountCheck(QuotaCheck):
    key = "ec2_on_demand_g_count"
    description = "Running On-Demand G EC2 instances"
    scope = QuotaScope.ACCOUNT
    service_code = "ec2"
    quota_code = "L-DB2E81BA"

    @property
    def current(self):
        instances = get_all_running_ec2_instances(self.boto_session)

        return len(list(filter(lambda inst: inst['InstanceType'][0] in ['g'], instances)))


class OnDemandInfInstanceCountCheck(QuotaCheck):
    key = "ec2_on_demand_inf_count"
    description = "Running On-Demand Inf EC2 instances"
    scope = QuotaScope.ACCOUNT
    service_code = "ec2"
    quota_code = "L-1945791B"

    @property
    def current(self):
        instances = get_all_running_ec2_instances(self.boto_session)

        return len(list(filter(lambda inst: inst['InstanceType'][0] in ['inf'], instances)))


class OnDemandPInstanceCountCheck(QuotaCheck):
    key = "ec2_on_demand_p_count"
    description = "Running On-Demand P EC2 instances"
    scope = QuotaScope.ACCOUNT
    service_code = "ec2"
    quota_code = "L-417A185B"

    @property
    def current(self):
        instances = get_all_running_ec2_instances(self.boto_session)

        return len(list(filter(lambda inst: inst['InstanceType'][0] in ['p'], instances)))


class OnDemandXInstanceCountCheck(QuotaCheck):
    key = "ec2_on_demand_x_count"
    description = "Running On-Demand X EC2 instances"
    scope = QuotaScope.ACCOUNT
    service_code = "ec2"
    quota_code = "L-7295265B"

    @property
    def current(self):
        instances = get_all_running_ec2_instances(self.boto_session)

        return len(list(filter(lambda inst: inst['InstanceType'][0] in ['x'], instances)))


class SpotStandardRequestCountCheck(QuotaCheck):
    key = "ec2_spot_standard_count"
    description = "All Standard (A, C, D, H, I, M, R, T, Z) EC2 Spot Instance Requests"
    scope = QuotaScope.ACCOUNT
    service_code = "ec2"
    quota_code = "L-34B43A08"

    @property
    def current(self):
        requests = get_all_spot_requests(self.boto_session)

        return len(list(filter(lambda inst: inst['LaunchSpecification']['InstanceType'][0] in ['a', 'c', 'd', 'h', 'i', 'm', 'r', 't', 'z'], requests)))


class SpotFRequestCountCheck(QuotaCheck):
    key = "ec2_spot_f_count"
    description = "All F EC2 Spot Instance Requests"
    scope = QuotaScope.ACCOUNT
    service_code = "ec2"
    quota_code = "L-88CF9481"

    @property
    def current(self):
        requests = get_all_spot_requests(self.boto_session)

        return len(list(filter(lambda inst: inst['LaunchSpecification']['InstanceType'][0] in ['f'], requests)))


class SpotGRequestCountCheck(QuotaCheck):
    key = "ec2_spot_g_count"
    description = "All G EC2 Spot Instance Requests"
    scope = QuotaScope.ACCOUNT
    service_code = "ec2"
    quota_code = "L-3819A6DF"

    @property
    def current(self):
        requests = get_all_spot_requests(self.boto_session)

        return len(list(filter(lambda inst: inst['LaunchSpecification']['InstanceType'][0] in ['g'], requests)))


class SpotInfRequestCountCheck(QuotaCheck):
    key = "ec2_spot_inf_count"
    description = "All Inf EC2 Spot Instance Requests"
    scope = QuotaScope.ACCOUNT
    service_code = "ec2"
    quota_code = "L-B5D1601B"

    @property
    def current(self):
        requests = get_all_spot_requests(self.boto_session)

        return len(list(filter(lambda inst: inst['LaunchSpecification']['InstanceType'][0] in ['inf'], requests)))


class SpotPRequestCountCheck(QuotaCheck):
    key = "ec2_spot_p_count"
    description = "All P EC2 Spot Instance Requests"
    scope = QuotaScope.ACCOUNT
    service_code = "ec2"
    quota_code = "L-7212CCBC"

    @property
    def current(self):
        requests = get_all_spot_requests(self.boto_session)

        return len(list(filter(lambda inst: inst['LaunchSpecification']['InstanceType'][0] in ['p'], requests)))


class SpotXRequestCountCheck(QuotaCheck):
    key = "ec2_spot_x_count"
    description = "All X EC2 Spot Instance Requests"
    scope = QuotaScope.ACCOUNT
    service_code = "ec2"
    quota_code = "L-E3A00192"

    @property
    def current(self):
        requests = get_all_spot_requests(self.boto_session)

        return len(list(filter(lambda inst: inst['LaunchSpecification']['InstanceType'][0] in ['x'], requests)))


class ElasticIpCountCheck(QuotaCheck):
    key = "ec2_eip_count"
    description = "EC2 VPC Elastic IPs"
    scope = QuotaScope.ACCOUNT
    service_code = 'ec2'
    quota_code = 'L-0263D0A3'

    @property
    def current(self):
        return len(self.boto_session.client('ec2').describe_addresses()['Addresses'])


class TransitGatewayCountCheck(QuotaCheck):
    key = "ec2_tgw_count"
    description = "Transit Gateways per Account"
    scope = QuotaScope.ACCOUNT
    service_code = 'ec2'
    quota_code = 'L-A2478D36'

    @property
    def current(self):
        return len(self.boto_session.client('ec2').describe_transit_gateways()['TransitGateways'])


class VpnConnectionCountCheck(QuotaCheck):
    key = "ec2_vpn_connection_count"
    description = "VPN connections per Region"
    scope = QuotaScope.REGION
    service_code = 'ec2'
    quota_code = 'L-3E6EC3A3'

    @property
    def current(self):
        return len(self.boto_session.client('ec2').describe_vpn_connections()['VpnConnections'])
