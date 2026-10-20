import asyncio
import argparse
import os
from sqlalchemy import select, delete, func

from app.database import AsyncSessionLocal
from app.security import hash_password

from app.models import (
    User,
    UserRole,
    Branch,
    Technician,
    Atm,
    AtmStatus,
    ServiceCall,
    ServiceCallPriority,
    ServiceCallStatus,
    DiagnosticReport,
)


SEED_USERS = ['alice.admin', 'robert.admin', 'jennifer.admin', 'michael.admin', 'marcus.audit', 'sarah.tech', 'james.tech', 'emily.tech', 'daniel.tech', 'olivia.tech', 'noah.tech', 'sophia.tech', 'ethan.tech', 'ava.tech']
SEED_ATMS = ['ATM-ATL-001', 'ATM-ATL-002', 'ATM-ATL-003', 'ATM-ATL-004', 'ATM-ATL-005', 'ATM-NGA-001', 'ATM-NGA-002', 'ATM-NGA-003', 'ATM-NGA-004', 'ATM-NGA-005', 'ATM-SGA-001', 'ATM-SGA-002', 'ATM-SGA-003', 'ATM-SGA-004', 'ATM-WGA-001', 'ATM-WGA-002', 'ATM-WGA-003', 'ATM-WGA-004']
SEED_BRANCHES = ['Atlanta Central', 'North Georgia', 'South Georgia', 'West Georgia']


async def remove_seed_data(session):
    # Delete child records first. All changes are in one transaction.
    user_ids = (await session.scalars(select(User.id).where(User.username.in_(SEED_USERS)))).all()
    atm_ids = (await session.scalars(select(Atm.id).where(Atm.serial_number.in_(SEED_ATMS)))).all()
    call_ids = (await session.scalars(select(ServiceCall.id).where(ServiceCall.atm_id.in_(atm_ids)))).all() if atm_ids else []
    if call_ids:
        await session.execute(delete(DiagnosticReport).where(DiagnosticReport.service_call_id.in_(call_ids)))
        await session.execute(delete(ServiceCall).where(ServiceCall.id.in_(call_ids)))
    if atm_ids:
        await session.execute(delete(Atm).where(Atm.id.in_(atm_ids)))
    if user_ids:
        await session.execute(delete(Technician).where(Technician.user_id.in_(user_ids)))
    await session.execute(delete(Branch).where(Branch.name.in_(SEED_BRANCHES)))
    if user_ids:
        await session.execute(delete(User).where(User.id.in_(user_ids)))


async def seed_database(reset=False):
    password = os.environ.get("SEED_USER_PASSWORD")
    if not password:
        raise RuntimeError("SEED_USER_PASSWORD is missing from the environment")
    async with AsyncSessionLocal() as session:
        async with session.begin():
            if reset:
                await remove_seed_data(session)
            else:
                existing = await session.scalar(
                    select(func.count()).select_from(Atm).where(Atm.serial_number.in_(SEED_ATMS))
                )
                if existing:
                    if existing != len(SEED_ATMS):
                        raise RuntimeError("Seed data is incomplete; use --reset to rebuild it")
                    print("Seed data already exists. Skipping.")
                    return

            # USERS

            users = [
                # Operations Admins / Branch Supervisors
                User(
                    name="Alice Johnson",
                    username="alice.admin",
                    hashed_password=hash_password(password),
                    role=UserRole.OPERATIONS_ADMIN,
                ),
                User(
                    name="Robert Wilson",
                    username="robert.admin",
                    hashed_password=hash_password(password),
                    role=UserRole.OPERATIONS_ADMIN,
                ),
                User(
                    name="Jennifer Thompson",
                    username="jennifer.admin",
                    hashed_password=hash_password(password),
                    role=UserRole.OPERATIONS_ADMIN,
                ),
                User(
                    name="Michael Harris",
                    username="michael.admin",
                    hashed_password=hash_password(password),
                    role=UserRole.OPERATIONS_ADMIN,
                ),

                # Auditor
                User(
                    name="Marcus Lee",
                    username="marcus.audit",
                    hashed_password=hash_password(password),
                    role=UserRole.AUDITOR,
                ),

                # Field Technicians
                User(
                    name="Sarah Williams",
                    username="sarah.tech",
                    hashed_password=hash_password(password),
                    role=UserRole.FIELD_TECHNICIAN,
                ),
                User(
                    name="James Carter",
                    username="james.tech",
                    hashed_password=hash_password(password),
                    role=UserRole.FIELD_TECHNICIAN,
                ),
                User(
                    name="Emily Davis",
                    username="emily.tech",
                    hashed_password=hash_password(password),
                    role=UserRole.FIELD_TECHNICIAN,
                ),
                User(
                    name="Daniel Brown",
                    username="daniel.tech",
                    hashed_password=hash_password(password),
                    role=UserRole.FIELD_TECHNICIAN,
                ),
                User(
                    name="Olivia Miller",
                    username="olivia.tech",
                    hashed_password=hash_password(password),
                    role=UserRole.FIELD_TECHNICIAN,
                ),
                User(
                    name="Noah Anderson",
                    username="noah.tech",
                    hashed_password=hash_password(password),
                    role=UserRole.FIELD_TECHNICIAN,
                ),
                User(
                    name="Sophia Martinez",
                    username="sophia.tech",
                    hashed_password=hash_password(password),
                    role=UserRole.FIELD_TECHNICIAN,
                ),
                User(
                    name="Ethan Clark",
                    username="ethan.tech",
                    hashed_password=hash_password(password),
                    role=UserRole.FIELD_TECHNICIAN,
                ),
                User(
                    name="Ava Robinson",
                    username="ava.tech",
                    hashed_password=hash_password(password),
                    role=UserRole.FIELD_TECHNICIAN,
                ),
            ]

            session.add_all(users)
            await session.flush()



            # BRANCHES

            branches = [
                Branch(
                    name="Atlanta Central",
                    location_region="Atlanta Metro",
                    capacity=10,
                    supervisor_id=users[0].id,
                ),
                Branch(
                    name="North Georgia",
                    location_region="North Georgia",
                    capacity=10,
                    supervisor_id=users[1].id,
                ),
                Branch(
                    name="South Georgia",
                    location_region="South Georgia",
                    capacity=8,
                    supervisor_id=users[2].id,
                ),
                Branch(
                    name="West Georgia",
                    location_region="West Georgia",
                    capacity=8,
                    supervisor_id=users[3].id,
                ),
            ]

            session.add_all(branches)
            await session.flush()



            # TECHNICIANS

            technicians = [

                Technician(
                    name=users[5].name,
                    user_id=users[5].id,
                    branch_id=branches[0].id,
                ),
                Technician(
                    name=users[6].name,
                    user_id=users[6].id,
                    branch_id=branches[0].id,
                ),
                Technician(
                    name=users[7].name,
                    user_id=users[7].id,
                    branch_id=branches[0].id,
                ),


                Technician(
                    name=users[8].name,
                    user_id=users[8].id,
                    branch_id=branches[1].id,
                ),
                Technician(
                    name=users[9].name,
                    user_id=users[9].id,
                    branch_id=branches[1].id,
                ),
                Technician(
                    name=users[10].name,
                    user_id=users[10].id,
                    branch_id=branches[1].id,
                ),


                Technician(
                    name=users[11].name,
                    user_id=users[11].id,
                    branch_id=branches[2].id,
                ),
                Technician(
                    name=users[12].name,
                    user_id=users[12].id,
                    branch_id=branches[2].id,
                ),


                Technician(
                    name=users[13].name,
                    user_id=users[13].id,
                    branch_id=branches[3].id,
                ),
            ]

            session.add_all(technicians)
            await session.flush()



            # ATMS

            atms = [

                Atm(
                    serial_number="ATM-ATL-001",
                    model="NCR-80",
                    status=AtmStatus.OPERATIONAL,
                    cash_level=8500,
                    branch_id=branches[0].id,
                ),
                Atm(
                    serial_number="ATM-ATL-002",
                    model="NCR-80",
                    status=AtmStatus.MAINTENANCE,
                    cash_level=2100,
                    branch_id=branches[0].id,
                ),
                Atm(
                    serial_number="ATM-ATL-003",
                    model="Diebold-20",
                    status=AtmStatus.OPERATIONAL,
                    cash_level=12500,
                    branch_id=branches[0].id,
                ),
                Atm(
                    serial_number="ATM-ATL-004",
                    model="Diebold-20",
                    status=AtmStatus.OPERATIONAL,
                    cash_level=7000,
                    branch_id=branches[0].id,
                ),
                Atm(
                    serial_number="ATM-ATL-005",
                    model="NCR-90",
                    status=AtmStatus.OPERATIONAL,
                    cash_level=9500,
                    branch_id=branches[0].id,
                ),

            

                Atm(
                    serial_number="ATM-NGA-001",
                    model="Diebold-20",
                    status=AtmStatus.OPERATIONAL,
                    cash_level=4500,
                    branch_id=branches[1].id,
                ),
                Atm(
                    serial_number="ATM-NGA-002",
                    model="NCR-90",
                    status=AtmStatus.IN_TRANSPORT,
                    cash_level=0,
                    branch_id=branches[1].id,
                ),
                Atm(
                    serial_number="ATM-NGA-003",
                    model="NCR-90",
                    status=AtmStatus.MAINTENANCE,
                    cash_level=3000,
                    branch_id=branches[1].id,
                ),
                Atm(
                    serial_number="ATM-NGA-004",
                    model="NCR-80",
                    status=AtmStatus.OPERATIONAL,
                    cash_level=18000,
                    branch_id=branches[1].id,
                ),
                Atm(
                    serial_number="ATM-NGA-005",
                    model="Diebold-20",
                    status=AtmStatus.OPERATIONAL,
                    cash_level=1500,
                    branch_id=branches[1].id,
                ),

            

                Atm(
                    serial_number="ATM-SGA-001",
                    model="NCR-80",
                    status=AtmStatus.OPERATIONAL,
                    cash_level=9000,
                    branch_id=branches[2].id,
                ),
                Atm(
                    serial_number="ATM-SGA-002",
                    model="NCR-80",
                    status=AtmStatus.MAINTENANCE,
                    cash_level=2000,
                    branch_id=branches[2].id,
                ),
                Atm(
                    serial_number="ATM-SGA-003",
                    model="NCR-90",
                    status=AtmStatus.MAINTENANCE,
                    cash_level=2500,
                    branch_id=branches[2].id,
                ),
                Atm(
                    serial_number="ATM-SGA-004",
                    model="Diebold-20",
                    status=AtmStatus.MAINTENANCE,
                    cash_level=1800,
                    branch_id=branches[2].id,
                ),

            

                Atm(
                    serial_number="ATM-WGA-001",
                    model="Diebold-20",
                    status=AtmStatus.OPERATIONAL,
                    cash_level=14000,
                    branch_id=branches[3].id,
                ),
                Atm(
                    serial_number="ATM-WGA-002",
                    model="NCR-90",
                    status=AtmStatus.OPERATIONAL,
                    cash_level=4000,
                    branch_id=branches[3].id,
                ),
                Atm(
                    serial_number="ATM-WGA-003",
                    model="NCR-80",
                    status=AtmStatus.OFFLINE,
                    cash_level=1000,
                    branch_id=branches[3].id,
                ),
                Atm(
                    serial_number="ATM-WGA-004",
                    model="Diebold-20",
                    status=AtmStatus.OPERATIONAL,
                    cash_level=11000,
                    branch_id=branches[3].id,
                ),
            ]

            session.add_all(atms)
            await session.flush()



            # SERVICE CALLS

            service_calls = [


                ServiceCall(
                    title="ATM dispensing cash incorrectly",
                    priority=ServiceCallPriority.CRITICAL,
                    status=ServiceCallStatus.IN_PROGRESS,
                    atm_id=atms[0].id,
                    technician_id=technicians[0].id,
                ),
                ServiceCall(
                    title="Card reader malfunction",
                    priority=ServiceCallPriority.MEDIUM,
                    status=ServiceCallStatus.PENDING,
                    atm_id=atms[1].id,
                    technician_id=technicians[1].id,
                ),
                ServiceCall(
                    title="Routine cash dispenser inspection",
                    priority=ServiceCallPriority.LOW,
                    status=ServiceCallStatus.COMPLETED,
                    atm_id=atms[2].id,
                    technician_id=technicians[0].id,
                ),
                ServiceCall(
                    title="ATM network connection failure",
                    priority=ServiceCallPriority.CRITICAL,
                    status=ServiceCallStatus.FAILED,
                    atm_id=atms[3].id,
                    technician_id=technicians[1].id,
                ),
                ServiceCall(
                    title="Preventative maintenance inspection",
                    priority=ServiceCallPriority.LOW,
                    status=ServiceCallStatus.COMPLETED,
                    atm_id=atms[4].id,
                    technician_id=technicians[2].id,
                ),



                ServiceCall(
                    title="Low cash warning",
                    priority=ServiceCallPriority.MEDIUM,
                    status=ServiceCallStatus.IN_PROGRESS,
                    atm_id=atms[5].id,
                    technician_id=technicians[3].id,
                ),
                ServiceCall(
                    title="ATM diagnostic failure",
                    priority=ServiceCallPriority.CRITICAL,
                    status=ServiceCallStatus.FAILED,
                    atm_id=atms[7].id,
                    technician_id=technicians[4].id,
                ),
                ServiceCall(
                    title="Cash dispenser inspection",
                    priority=ServiceCallPriority.LOW,
                    status=ServiceCallStatus.COMPLETED,
                    atm_id=atms[8].id,
                    technician_id=technicians[3].id,
                ),
                ServiceCall(
                    title="Emergency cash refill",
                    priority=ServiceCallPriority.CRITICAL,
                    status=ServiceCallStatus.PENDING,
                    atm_id=atms[9].id,
                    technician_id=technicians[5].id,
                ),




                ServiceCall(
                    title="ATM screen malfunction",
                    priority=ServiceCallPriority.MEDIUM,
                    status=ServiceCallStatus.COMPLETED,
                    atm_id=atms[10].id,
                    technician_id=technicians[6].id,
                ),
                ServiceCall(
                    title="Hardware replacement",
                    priority=ServiceCallPriority.CRITICAL,
                    status=ServiceCallStatus.IN_PROGRESS,
                    atm_id=atms[11].id,
                    technician_id=technicians[7].id,
                ),
                ServiceCall(
                    title="ATM maintenance diagnostic",
                    priority=ServiceCallPriority.MEDIUM,
                    status=ServiceCallStatus.FAILED,
                    atm_id=atms[12].id,
                    technician_id=technicians[6].id,
                ),
                ServiceCall(
                    title="Dispenser motor replacement",
                    priority=ServiceCallPriority.CRITICAL,
                    status=ServiceCallStatus.PENDING,
                    atm_id=atms[13].id,
                    technician_id=technicians[7].id,
                ),




                ServiceCall(
                    title="Routine inspection",
                    priority=ServiceCallPriority.LOW,
                    status=ServiceCallStatus.COMPLETED,
                    atm_id=atms[14].id,
                    technician_id=technicians[8].id,
                ),
                ServiceCall(
                    title="Cash dispenser issue",
                    priority=ServiceCallPriority.MEDIUM,
                    status=ServiceCallStatus.FAILED,
                    atm_id=atms[15].id,
                    technician_id=technicians[8].id,
                ),
                ServiceCall(
                    title="ATM recovery procedure",
                    priority=ServiceCallPriority.CRITICAL,
                    status=ServiceCallStatus.IN_PROGRESS,
                    atm_id=atms[16].id,
                    technician_id=technicians[8].id,
                ),
                ServiceCall(
                    title="Preventative inspection",
                    priority=ServiceCallPriority.LOW,
                    status=ServiceCallStatus.COMPLETED,
                    atm_id=atms[17].id,
                    technician_id=technicians[8].id,
                ),



                # CO-LOCATION DISCREPANCIES

                ServiceCall(
                    title="Cross-branch emergency repair",
                    priority=ServiceCallPriority.CRITICAL,
                    status=ServiceCallStatus.IN_PROGRESS,
                    atm_id=atms[0].id,
                    technician_id=technicians[3].id,
                ),
                ServiceCall(
                    title="Regional emergency dispatch",
                    priority=ServiceCallPriority.MEDIUM,
                    status=ServiceCallStatus.PENDING,
                    atm_id=atms[10].id,
                    technician_id=technicians[0].id,
                ),
                ServiceCall(
                    title="Specialized ATM repair",
                    priority=ServiceCallPriority.CRITICAL,
                    status=ServiceCallStatus.COMPLETED,
                    atm_id=atms[14].id,
                    technician_id=technicians[6].id,
                ),
            ]

            session.add_all(service_calls)
            await session.flush()



            # DIAGNOSTIC REPORTS

            reports = [
                DiagnosticReport(
                    file_url="/reports/sc-001-initial.pdf",
                    notes="Dispenser motor showing intermittent errors.",
                    service_call_id=service_calls[0].id,
                    technician_id=technicians[0].id,
                ),
                DiagnosticReport(
                    file_url="/reports/sc-001-followup.pdf",
                    notes="Motor replaced and tested successfully.",
                    service_call_id=service_calls[0].id,
                    technician_id=technicians[0].id,
                ),
                DiagnosticReport(
                    file_url="/reports/sc-003-complete.pdf",
                    notes="Routine inspection completed with no major issues.",
                    service_call_id=service_calls[2].id,
                    technician_id=technicians[0].id,
                ),
                DiagnosticReport(
                    file_url="/reports/sc-006-diagnostic.pdf",
                    notes="Low cash condition confirmed.",
                    service_call_id=service_calls[5].id,
                    technician_id=technicians[3].id,
                ),
                DiagnosticReport(
                    file_url="/reports/sc-007-diagnostic.pdf",
                    notes="Hardware diagnostic indicates dispenser failure.",
                    service_call_id=service_calls[6].id,
                    technician_id=technicians[4].id,
                ),
                DiagnosticReport(
                    file_url="/reports/sc-011-maintenance.pdf",
                    notes="Hardware replacement required.",
                    service_call_id=service_calls[10].id,
                    technician_id=technicians[7].id,
                ),
                DiagnosticReport(
                    file_url="/reports/sc-012-diagnostic.pdf",
                    notes="Maintenance diagnostic completed.",
                    service_call_id=service_calls[11].id,
                    technician_id=technicians[6].id,
                ),
                DiagnosticReport(
                    file_url="/reports/sc-016-recovery.pdf",
                    notes="ATM recovered after network reset.",
                    service_call_id=service_calls[15].id,
                    technician_id=technicians[8].id,
                ),
            ]

            session.add_all(reports)

    print("Database seeded successfully!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()
    asyncio.run(seed_database(reset=args.reset))
