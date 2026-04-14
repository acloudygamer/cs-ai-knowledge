# KD-Tree

## 核心概念

K-Dimension Tree，高维数据索引结构，用于 k 维空间中的最近邻搜索、范围查询等。

## 基本原理

- 每个节点代表 k 维空间中的一个点
- 交替使用各维度作为划分依据（第 i 层用第 i % k 维）
- 左子树在划分维度上小于当前节点，右子树大于
- 类似 BST，但维度交替

## 实现

```python
class KDNode:
    def __init__(self, point, dim):
        self.point = point  # k维点
        self.dim = dim      # 划分的维度
        self.left = None
        self.right = None


class KDTree:
    def __init__(self, k=2):
        self.k = k
        self.root = None

    def build(self, points):
        """构建 KD-Tree"""
        def build_node(points, depth):
            if not points:
                return None

            # 交替选择维度
            dim = depth % self.k
            points.sort(key=lambda x: x[dim])
            mid = len(points) // 2

            node = KDNode(points[mid], dim)
            node.left = build_node(points[:mid], depth + 1)
            node.right = build_node(points[mid + 1:], depth + 1)
            return node

        self.root = build_node(points, 0)
        return self.root

    def insert(self, point):
        """插入点"""
        def insert_node(node, point, depth):
            if node is None:
                return KDNode(point, depth % self.k)

            dim = depth % self.k
            if point[dim] < node.point[dim]:
                node.left = insert_node(node.left, point, depth + 1)
            else:
                node.right = insert_node(node.right, point, depth + 1)
            return node

        self.root = insert_node(self.root, point, 0)

    def search(self, target):
        """搜索最近邻"""
        def search_nearest(node, target, depth, best):
            if node is None:
                return best

            dim = depth % self.k
            dist = self._distance(node.point, target)

            if dist < self._distance(best, target):
                best = node.point

            # 先搜索可能包含最近点的子树
            if target[dim] < node.point[dim]:
                next_branch = node.left
                other_branch = node.right
            else:
                next_branch = node.right
                other_branch = node.left

            best = search_nearest(next_branch, target, depth + 1, best)

            # 检查另一个分支是否可能包含更近的点
            if abs(target[dim] - node.point[dim]) < self._distance(best, target):
                best = search_nearest(other_branch, target, depth + 1, best)

            return best

        if self.root is None:
            return None
        return search_nearest(self.root, target, 0, self.root.point)

    def range_query(self, lo, hi):
        """范围查询：返回在 [lo, hi] 范围内的所有点"""
        result = []

        def query_node(node, bounds, depth):
            if node is None:
                return

            dim = depth % self.k
            point = node.point

            # 检查当前点是否在范围内
            in_bounds = all(lo[i] <= point[i] <= hi[i] for i in range(self.k))
            if in_bounds:
                result.append(point)

            # 递归搜索子树
            if point[dim] >= lo[dim]:
                query_node(node.left, bounds, depth + 1)
            if point[dim] <= hi[dim]:
                query_node(node.right, bounds, depth + 1)

        query_node(self.root, (lo, hi), 0)
        return result

    @staticmethod
    def _distance(p1, p2):
        """欧氏距离"""
        return sum((a - b) ** 2 for a, b in zip(p1, p2)) ** 0.5
```

## 最近邻搜索

```python
def k_nearest_neighbors(tree, target, k=1):
    """找 k 个最近邻"""
    candidates = []

    def search(node, depth):
        if node is None:
            return

        dim = depth % tree.k
        point = node.point
        dist = tree._distance(point, target)

        # 维护大小为 k 的最大堆
        if len(candidates) < k:
            candidates.append((dist, point))
            candidates.sort(reverse=True)
        elif dist < candidates[0][0]:
            candidates[0] = (dist, point)
            candidates.sort(reverse=True)

        # 确定搜索顺序
        if target[dim] < point[dim]:
            near, far = node.left, node.right
        else:
            near, far = node.right, node.left

        search(near, depth + 1)

        # 检查是否需要搜索另一子树
        if len(candidates) < k or abs(target[dim] - point[dim]) < candidates[0][0]:
            search(far, depth + 1)

    search(tree.root, 0)
    return [p for _, p in sorted(candidates)]
```

## 应用场景

| 场景 | 说明 |
|------|------|
| 最近邻搜索 | 图像识别、推荐系统 |
| 范围查询 | 地理信息系统 (GIS) |
| 聚类分析 | K-Means 初始化 |
| 异常检测 | 寻找距离异常远的点 |
| 碰撞检测 | 游戏开发中的空间划分 |

## KD-Tree vs 其他结构

| 结构 | 适用维度 | 最近邻查询 | 范围查询 |
|------|---------|-----------|---------|
| KD-Tree | < 20 维 | O(log n) 平均 | 高效 |
| Ball Tree | 高维 | O(n^(1-1/d)) | 高效 |
| R-Tree | 2-3 维 | 高效 | 高效 |
| 暴力搜索 | 任意 | O(n) | O(n) |

## 局限性

- 高维情况下效率退化（维度灾难）
- 动态插入删除效率较低
- 适合静态数据集或定期重建