function make_mesh(outprefix, scale, sizefile, layout, itmax)
% MESAWAVE WW3 mesh: one global domain sized by a precomputed raster (regions.py):
% 25 km open ocean, 10 km coast, 12 km TC regions (convex hulls), 5 km US coasts.
% scale multiplies every element size (1 = production, 2 = tuning twin, 4 = smoke test).
% layout picks the initial points: 'rows' (latitude rows, Alper's) or 'icos' (subdivided icosahedron).
% itmax caps the DistMesh iterations (OceanMesh2D's default, 100, is always reached).
if nargin < 1, outprefix = 'mesawave'; end
if nargin < 2, scale = 1; end
if nargin < 3, sizefile = 'sizefx_na1000_ot500_hull.nc'; end
if nargin < 4, layout = 'rows'; end
if nargin < 5, itmax = 100; end

here = fileparts(mfilename('fullpath'));
om2d = fullfile(here, '..', 'OceanMesh2D');
addpath(om2d);
setup_oceanmesh2d;
addpath(fullfile(om2d, 'm_map'));  % setup_oceanmesh2d only finds m_map when run from om2d

dem   = fullfile(here, '..', 'data', 'GEBCO_2024_coarse_x4.nc');
gshhs = fullfile(om2d, 'datasets', 'GSHHS_shp', 'f');
% L5 is the Antarctic ice front; regions.py moves its pole closure to 81S
shp   = {fullfile(gshhs, 'GSHHS_f_L1'), fullfile(here, 'regions', 'GSHHS_f_L5_clamp81')};
bbox  = [-180 180; -80 90];  % open water ends ~78.7S
grade = 0.20;
min_depth = 5;   % m

szf = fullfile(here, 'regions', sizefile);
slon = ncread(szf, 'lon');
slat = ncread(szf, 'lat');
hsz  = double(ncread(szf, 'h')) * scale;   % [lon x lat], m
h0   = min(hsz(:));
lev  = size_levels(hsz);
fprintf('%s: scale %g, size raster %s, h %.0f-%.0f m\n', outprefix, scale, sizefile, h0, max(hsz(:)));

gd = geodata('shp', shp, 'dem', dem, 'bbox', bbox, 'h0', h0);
ef = edgefx('geodata', gd, 'max_el', max(hsz(:)), 'g', grade);
% the raster is graded by construction; use it as the edge function
[LON, LAT] = ndgrid(slon, slat);
ef.F = griddedInterpolant(LON, LAT, hsz, 'linear', 'nearest');
clear LON LAT hsz

mg = meshgen('ef', ef, 'bou', gd, 'proj', 'stereo', 'plot_on', 0, 'nscreen', 10, 'itmax', itmax);
% OM2D's own initial points are ~35% too sparse and never corrected; supply ours
if strcmp(layout, 'icos')
    mg.grd.p = initial_points_icos(ef.F, lev, bbox(2, :));
else
    mg.grd.p = initial_points(ef.F, lev, bbox(2, :));
end
mg.grd.p = mg.grd.p(feval(mg.fd, mg.grd.p, mg, 1) < 0, :);
fprintf('%s: %d initial points\n', outprefix, size(mg.grd.p, 1));
mg = mg.build;
m = mg.grd;
m = interp(m, dem);              % cell-averaged depth, positive down
m.b = max(m.b, min_depth);

save([outprefix '_msh.mat'], 'm', '-v7.3');
p = m.p; t = m.t; b = m.b;
save([outprefix '_ptb.mat'], 'p', 't', 'b', '-v7');
m.op = struct('nope', 0, 'neta', 0, 'nvdll', [], 'nbdv', []);  % global: no open boundaries
write(m, outprefix, 'ww3');
fprintf('%s: %d nodes, %d elements\n', outprefix, size(m.p, 1), size(m.t, 1));
end

function lev = size_levels(hsz)
% plateau sizes (min, max, any on >1% of cells), filled geometrically at <=10% steps
[u, ~, ic] = unique(hsz(:));
c = accumarray(ic, 1);
plat = unique([u(1); u(c > 0.01 * numel(hsz)); u(end)]);
lev = plat(1);
for i = 2:numel(plat)
    n = ceil(log(plat(i) / plat(i-1)) / log(1.1));
    lev = [lev; plat(i-1) * (plat(i) / plat(i-1)).^((1:n)' / n)]; %#ok<AGROW>
end
end

function p = initial_points(F, lev, latlim)
% one equilateral lattice per size level; a point is kept where its level is nearest the target
% (random thinning of a single lattice left the mesh disordered: 26% of nodes not 6-valent).
% Each row is staggered against the previous one at a golden-ratio longitude, so the
% row-length changes scatter instead of lining up on fixed meridians (0, +-45, ...).
R = 6378.137e3;
g = (sqrt(5) - 1) / 2;
llev = log(lev(:))';
p = cell(numel(lev), 1);
for k = 1:numel(lev)
    lat = (latlim(1):rad2deg(lev(k) * sqrt(3) / 2 / R):latlim(2))';
    q = cell(numel(lat), 1);
    l0 = -180; s0 = [];
    for i = 1:numel(lat)
        nx = max(1, round(2 * pi * R * cosd(lat(i)) / lev(k)));
        s = 360 / nx;
        if ~isempty(s0)
            l0 = l0 + (floor((-180 + 360 * mod(i * g, 1) - l0) / s0) + 0.5) * s0;
        end
        s0 = s;
        lon = mod(l0 + (0:nx-1)' * s + 180, 360) - 180;
        r = [lon, repmat(lat(i), nx, 1)];
        [~, kk] = min(abs(log(F(r)) - llev), [], 2);
        q{i} = r(kk == k, :);
    end
    p{k} = vertcat(q{:});
end
p = vertcat(p{:});
end

function p = initial_points_icos(F, lev, latlim)
% Same idea as initial_points (one lattice per size level, a point kept where its level is
% nearest the target), but each lattice is a subdivided icosahedron instead of latitude rows.
% Each of the 20 faces gets a flat triangle lattice with n points per edge; neighbouring faces
% match point for point, so every point has 6 neighbours except the 12 icosahedron corners.
% Sine (slerp) weights space the points evenly along every edge; edge lengths vary ~17%
% (max/min) before relaxation. Q, from tools/icos_rotation.py, puts 8 corners on land,
% 2 in refined ocean and 2 in 25 km open ocean; all levels share it, so the corners coincide.
R = 6378.137e3;
Q = [0.075167382938914 0.964218520584349 0.254229245178924; ...
     0.415351985385366 0.201506225285574 -0.887061423694884; ...
     -0.906549829175732 0.172272707453301 -0.385343381269434];
g = (1 + sqrt(5)) / 2;
V = [0 1 g; 0 -1 g; 0 1 -g; 0 -1 -g; 1 g 0; -1 g 0; 1 -g 0; -1 -g 0; g 0 1; -g 0 1; g 0 -1; -g 0 -1];
V = (V ./ vecnorm(V, 2, 2)) * Q';
T = convhulln(V);                                  % the 20 faces
Om = acos(dot(V(T(1, 1), :), V(T(1, 2), :)));      % edge angle, 63.4 deg
llev = log(lev(:))';
p = cell(numel(lev), 1);
for k = 1:numel(lev)
    % points per edge, from area: 10n^2+2 points at spacing h cover the sphere. (Edge arc / h
    % gives ~9% too coarse a mesh: a spherical face has 18% more area than a flat triangle.)
    n = max(1, round(R / lev(k) * sqrt(4 * pi / (5 * sqrt(3)))));
    [I, J] = ndgrid(0:n, 0:n);
    m = I + J <= n;
    W = sin([I(m), J(m), n - I(m) - J(m)] / n * Om);
    q = cell(20, 1);
    for f = 1:20
        X = W * V(T(f, :), :);
        X = X ./ vecnorm(X, 2, 2);
        r = [atan2d(X(:, 2), X(:, 1)), asind(X(:, 3))];
        [~, kk] = min(abs(log(F(r)) - llev), [], 2);
        q{f} = X(kk == k & r(:, 2) >= latlim(1), :);
    end
    X = uniquetol(vertcat(q{:}), 1e-9, 'ByRows', true, 'DataScale', 1);   % faces share edges
    p{k} = [atan2d(X(:, 2), X(:, 1)), asind(X(:, 3))];
end
p = vertcat(p{:});
end
