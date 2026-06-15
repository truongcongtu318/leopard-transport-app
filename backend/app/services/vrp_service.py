"""
VRP service — Google OR-Tools CVRP (Capacitated Vehicle Routing Problem) solver.

Used for optimizing multi-stop delivery routes for fleet dispatchers.
"""

from __future__ import annotations

import logging
import math
import time
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vrp import RouteOptimization

logger = logging.getLogger(__name__)

_HAS_ORTOOLS = False
try:
    from ortools.constraint_solver import pywrapcp, routing_enums_pb2

    _HAS_ORTOOLS = True
except ImportError:
    logger.warning("OR-Tools not available; VRP optimization will be disabled")


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Haversine distance in kilometres."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class VRPBatchOptimizationService:
    """Solves multi-vehicle, multi-stop routing problems using OR-Tools."""

    def __init__(self, db: AsyncSession | None = None) -> None:
        self.db = db

    async def optimize(
        self,
        vehicles: list[dict[str, Any]],
        stops: list[dict[str, Any]],
        depot_lat: float,
        depot_lng: float,
        solver_time_limit_s: int = 30,
        priority: str = "distance",
        requested_by: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """Run OR-Tools CVRP solver.

        Args:
            vehicles: List of vehicle definitions.
            stops: List of stop definitions.
            depot_lat/lng: Depot coordinates (start/end point).
            solver_time_limit_s: Max solver time in seconds.
            priority: Optimization target ("distance", "time", or "cost").
            requested_by: UUID of user requesting the optimization.

        Returns:
            Dict with solver status, routes, and metadata.
        """
        if not _HAS_ORTOOLS:
            return {
                "solver_status": "error",
                "total_distance_km": 0.0,
                "total_duration_min": 0.0,
                "num_vehicles_used": 0,
                "num_stops_optimized": 0,
                "solver_time_ms": 0,
                "routes": [],
                "unassigned_stops": [],
                "metadata": {"error": "OR-Tools not installed"},
            }

        start_time = time.time()
        num_vehicles = len(vehicles)
        num_stops = len(stops)

        # Build distance and time matrices
        all_nodes = [(depot_lat, depot_lng)] + [
            (s["latitude"], s["longitude"]) for s in stops
        ]
        n = len(all_nodes)

        distance_matrix: list[list[int]] = []
        time_matrix: list[list[int]] = []
        speed_kmh = 35.0  # Average freight truck speed

        for i in range(n):
            dist_row: list[int] = []
            time_row: list[int] = []
            for j in range(n):
                km = _haversine_km(
                    all_nodes[i][0], all_nodes[i][1],
                    all_nodes[j][0], all_nodes[j][1],
                )
                km *= 1.3  # Road factor
                dist_row.append(int(km * 1000))  # metres
                time_row.append(int(km / speed_kmh * 3600))  # seconds
            distance_matrix.append(dist_row)
            time_matrix.append(time_row)

        # Demands (weight in kg)
        demands = [0] + [int(s.get("weight_kg", 0)) for s in stops]
        vehicle_capacities = [int(v.get("max_payload_kg", 10000)) for v in vehicles]

        # Time windows (optional)
        # Convert to int minutes from midnight (simplified)
        time_windows = []
        for s in stops:
            tw_start = s.get("time_window_start")
            tw_end = s.get("time_window_end")
            if tw_start and tw_end:
                time_windows.append((0, 1440))  # All-day default for now
            else:
                time_windows.append((0, 1440))

        # Create routing model
        manager = pywrapcp.RoutingIndexManager(n, num_vehicles, 0)  # depot = 0
        routing = pywrapcp.RoutingModel(manager)

        # Distance callback
        def distance_callback(from_idx: int, to_idx: int) -> int:
            from_node = manager.IndexToNode(from_idx)
            to_node = manager.IndexToNode(to_idx)
            return distance_matrix[from_node][to_node]

        dist_cb_idx = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(dist_cb_idx)

        # Add capacity constraint
        def demand_callback(from_idx: int) -> int:
            from_node = manager.IndexToNode(from_idx)
            return demands[from_node]

        demand_cb_idx = routing.RegisterUnaryTransitCallback(demand_callback)
        routing.AddDimensionWithVehicleCapacity(
            demand_cb_idx,
            0,  # null capacity slack
            vehicle_capacities,  # vehicle max capacities
            True,  # start cumul to zero
            "Capacity",
        )

        # Search parameters
        search_params = pywrapcp.DefaultRoutingSearchParameters()
        search_params.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_params.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_params.time_limit.seconds = solver_time_limit_s
        search_params.log_search = False

        # Solve
        solution = routing.SolveWithParameters(search_params)
        solver_time_ms = int((time.time() - start_time) * 1000)

        if solution:
            status_str = "feasible"
            total_distance_km = 0.0
            total_duration_min = 0.0
            routes: list[dict[str, Any]] = []
            assigned_stops: set[int] = set()

            for vehicle_idx in range(num_vehicles):
                idx = routing.Start(vehicle_idx)
                route_stops: list[int] = []
                route_dist = 0.0
                prev_node = 0
                while not routing.IsEnd(idx):
                    node = manager.IndexToNode(idx)
                    if node != 0:
                        route_stops.append(node - 1)  # 0-indexed stops
                        assigned_stops.add(node - 1)
                    dist = distance_matrix[prev_node][node] / 1000.0
                    route_dist += dist
                    prev_node = node
                    idx = solution.Value(routing.NextVar(idx))
                # Return to depot
                if prev_node != 0:
                    route_dist += distance_matrix[prev_node][0] / 1000.0

                total_distance_km += route_dist
                route_duration = route_dist / speed_kmh * 60
                total_duration_min += route_duration

                load_kg = sum(demands[s + 1] for s in route_stops)

                vdef = vehicles[vehicle_idx]
                routes.append({
                    "vehicle_id": vdef.get("vehicle_id"),
                    "stop_order": route_stops,
                    "distance_km": round(route_dist, 1),
                    "duration_min": int(route_duration),
                    "load_kg": load_kg,
                })

            unassigned = [i for i in range(num_stops) if i not in assigned_stops]

            result_data = {
                "solver_status": status_str,
                "total_distance_km": round(total_distance_km, 1),
                "total_duration_min": round(total_duration_min, 1),
                "num_vehicles_used": num_vehicles,
                "num_stops_optimized": len(assigned_stops),
                "solver_time_ms": solver_time_ms,
                "routes": routes,
                "unassigned_stops": unassigned,
                "metadata": {
                    "solver": "OR-Tools CVRP",
                    "priority": priority,
                    "algorithm": "Path Cheapest Arc + GLS",
                },
            }
        else:
            result_data = {
                "solver_status": "infeasible",
                "total_distance_km": 0.0,
                "total_duration_min": 0.0,
                "num_vehicles_used": num_vehicles,
                "num_stops_optimized": 0,
                "solver_time_ms": solver_time_ms,
                "routes": [],
                "unassigned_stops": list(range(num_stops)),
                "metadata": {"solver": "OR-Tools CVRP", "status": "no solution found"},
            }

        # Persist result if we have a DB
        if self.db and requested_by:
            optimization_record = RouteOptimization(
                requested_by=requested_by,
                input_data={"vehicles": vehicles, "stops": stops},
                result_data=result_data,
                solver_status=result_data["solver_status"],
                total_distance_km=result_data["total_distance_km"],
                total_duration_min=int(result_data["total_duration_min"]),
                num_vehicles_used=result_data["num_vehicles_used"],
                num_stops_optimized=result_data["num_stops_optimized"],
                solver_time_ms=solver_time_ms,
            )
            self.db.add(optimization_record)
            await self.db.flush()

        return result_data
