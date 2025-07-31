#!/usr/bin/env python3
"""
MCP Memory Graph Visualizer

Creates visual representations of the MCP knowledge graph showing entities, relations, and observations.
"""

import os
import json
import networkx as nx
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Tuple, Any
import argparse
from collections import defaultdict


class MCPGraphVisualizer:
    """Visualizes MCP memory knowledge graph."""
    
    def __init__(self, memory_file: str = "data/mcp_memory.json"):
        """Initialize visualizer with MCP memory file."""
        self.memory_file = memory_file
        self.entities = []
        self.relations = []
        self.graph = nx.DiGraph()
        
        # Color scheme for different entity types
        self.entity_colors = {
            'person': '#FF6B6B',      # Red
            'concept': '#4ECDC4',     # Teal
            'project': '#45B7D1',     # Blue
            'place': '#96CEB4',       # Green
            'other': '#FECA57'        # Yellow
        }
        
        self.load_data()
        self.build_graph()
    
    def load_data(self):
        """Load entities and relations from MCP memory file."""
        if not os.path.exists(self.memory_file):
            print(f"❌ Memory file not found: {self.memory_file}")
            return
        
        entities = []
        relations = []
        
        try:
            with open(self.memory_file, 'r') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line.strip())
                        if data.get('type') == 'entity':
                            entities.append(data)
                        elif data.get('type') == 'relation':
                            relations.append(data)
            
            self.entities = entities
            self.relations = relations
            
            print(f"✅ Loaded {len(entities)} entities and {len(relations)} relations")
            
        except Exception as e:
            print(f"❌ Error loading MCP data: {e}")
    
    def build_graph(self):
        """Build NetworkX graph from entities and relations."""
        # Add entity nodes
        for entity in self.entities:
            name = entity['name']
            entity_type = entity.get('entityType', 'other')
            observations = entity.get('observations', [])
            
            # Create node with attributes
            self.graph.add_node(
                name,
                entity_type=entity_type,
                observations=observations,
                color=self.entity_colors.get(entity_type, '#CCCCCC'),
                size=max(10, len(observations) * 5 + 10)  # Size based on observations count
            )
        
        # Add relation edges
        for relation in self.relations:
            from_entity = relation['from']
            to_entity = relation['to']
            relation_type = relation['relationType']
            
            # Only add edge if both entities exist
            if from_entity in self.graph.nodes and to_entity in self.graph.nodes:
                self.graph.add_edge(
                    from_entity,
                    to_entity,
                    relation=relation_type,
                    label=relation_type
                )
    
    def create_static_visualization(self, output_file: str = "mcp_graph.png", figsize: Tuple[int, int] = (15, 12)):
        """Create static matplotlib visualization."""
        if not self.graph.nodes:
            print("❌ No graph data to visualize")
            return
        
        plt.figure(figsize=figsize)
        
        # Use spring layout for better node positioning
        pos = nx.spring_layout(self.graph, k=3, iterations=50)
        
        # Group nodes by type for coloring
        entity_types = defaultdict(list)
        for node in self.graph.nodes(data=True):
            entity_types[node[1]['entity_type']].append(node[0])
        
        # Draw nodes by type
        for entity_type, nodes in entity_types.items():
            nx.draw_networkx_nodes(
                self.graph,
                pos,
                nodelist=nodes,
                node_color=self.entity_colors.get(entity_type, '#CCCCCC'),
                node_size=[self.graph.nodes[node]['size'] for node in nodes],
                alpha=0.8,
                label=entity_type
            )
        
        # Draw edges
        nx.draw_networkx_edges(
            self.graph,
            pos,
            edge_color='gray',
            arrows=True,
            arrowsize=20,
            alpha=0.6,
            width=1.5,
            arrowstyle='->'
        )
        
        # Draw labels
        nx.draw_networkx_labels(
            self.graph,
            pos,
            font_size=8,
            font_weight='bold'
        )
        
        # Draw edge labels (relation types)
        edge_labels = nx.get_edge_attributes(self.graph, 'relation')
        nx.draw_networkx_edge_labels(
            self.graph,
            pos,
            edge_labels,
            font_size=6,
            alpha=0.7
        )
        
        plt.title("MCP Memory Knowledge Graph", fontsize=16, fontweight='bold')
        plt.legend(scatterpoints=1, loc='upper right')
        plt.axis('off')
        plt.tight_layout()
        
        # Save the plot
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✅ Static visualization saved to: {output_file}")
        
        # Show the plot
        plt.show()
    
    def create_interactive_visualization(self, output_file: str = "mcp_graph.html"):
        """Create interactive Plotly visualization."""
        if not self.graph.nodes:
            print("❌ No graph data to visualize")
            return
        
        # Use spring layout
        pos = nx.spring_layout(self.graph, k=3, iterations=50)
        
        # Prepare node data
        node_x = []
        node_y = []
        node_text = []
        node_colors = []
        node_sizes = []
        node_info = []
        
        for node in self.graph.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            
            node_data = self.graph.nodes[node]
            entity_type = node_data['entity_type']
            observations = node_data.get('observations', [])
            
            # Node hover info
            obs_text = "<br>".join(observations[:3]) if observations else "No observations"
            if len(observations) > 3:
                obs_text += f"<br>... and {len(observations) - 3} more"
            
            node_info.append(
                f"<b>{node}</b><br>"
                f"Type: {entity_type}<br>"
                f"Observations: {len(observations)}<br>"
                f"{obs_text}"
            )
            
            node_text.append(node)
            node_colors.append(self.entity_colors.get(entity_type, '#CCCCCC'))
            node_sizes.append(max(10, len(observations) * 2 + 10))
        
        # Prepare edge data
        edge_x = []
        edge_y = []
        edge_info = []
        
        for edge in self.graph.edges():
            from_node, to_node = edge
            x0, y0 = pos[from_node]
            x1, y1 = pos[to_node]
            
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            
            relation = self.graph.edges[edge].get('relation', 'unknown')
            edge_info.append(f"{from_node} → {to_node}<br>Relation: {relation}")
        
        # Create the plot
        fig = go.Figure()
        
        # Add edges
        fig.add_trace(go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=2, color='rgba(125,125,125,0.5)'),
            hoverinfo='none',
            mode='lines',
            showlegend=False
        ))
        
        # Add nodes
        fig.add_trace(go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            marker=dict(
                size=node_sizes,
                color=node_colors,
                line=dict(width=2, color='rgba(50,50,50,0.5)'),
                opacity=0.8
            ),
            text=node_text,
            textposition="middle center",
            textfont=dict(size=10, color='white'),
            hoverinfo='text',
            hovertext=node_info,
            showlegend=False
        ))
        
        # Update layout
        fig.update_layout(
            title={
                'text': "MCP Memory Knowledge Graph (Interactive)",
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20}
            },
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20,l=5,r=5,t=40),
            annotations=[ 
                dict(
                    text=f"Entities: {len(self.entities)} | Relations: {len(self.relations)}",
                    showarrow=False,
                    xref="paper", yref="paper",
                    x=0, y=1, xanchor='left', yanchor='top',
                    font=dict(size=12)
                )
            ],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(245,245,245,1)'
        )
        
        # Save and show
        fig.write_html(output_file)
        print(f"✅ Interactive visualization saved to: {output_file}")
        fig.show()
    
    def print_graph_stats(self):
        """Print statistics about the knowledge graph."""
        print("\n📊 MCP Knowledge Graph Statistics:")
        print(f"   • Entities: {len(self.entities)}")
        print(f"   • Relations: {len(self.relations)}")
        print(f"   • Graph nodes: {len(self.graph.nodes)}")
        print(f"   • Graph edges: {len(self.graph.edges)}")
        
        # Entity type breakdown
        entity_type_counts = defaultdict(int)
        for entity in self.entities:
            entity_type_counts[entity.get('entityType', 'unknown')] += 1
        
        print("\n📋 Entity Types:")
        for entity_type, count in sorted(entity_type_counts.items()):
            print(f"   • {entity_type}: {count}")
        
        # Top entities by connections
        if self.graph.nodes:
            node_degrees = dict(self.graph.degree())
            top_nodes = sorted(node_degrees.items(), key=lambda x: x[1], reverse=True)[:5]
            
            print("\n🔗 Most Connected Entities:")
            for node, degree in top_nodes:
                print(f"   • {node}: {degree} connections")


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(description="Visualize MCP memory knowledge graph")
    parser.add_argument("--memory-file", default="data/mcp_memory.json",
                      help="Path to MCP memory file")
    parser.add_argument("--static", action="store_true",
                      help="Create static matplotlib visualization")
    parser.add_argument("--interactive", action="store_true", 
                      help="Create interactive Plotly visualization")
    parser.add_argument("--stats", action="store_true",
                      help="Print graph statistics")
    parser.add_argument("--output", default="mcp_graph",
                      help="Output file prefix")
    
    args = parser.parse_args()
    
    # Default to interactive if no specific type chosen
    if not args.static and not args.interactive:
        args.interactive = True
    
    visualizer = MCPGraphVisualizer(args.memory_file)
    
    if args.stats:
        visualizer.print_graph_stats()
    
    if args.static:
        visualizer.create_static_visualization(f"{args.output}.png")
    
    if args.interactive:
        visualizer.create_interactive_visualization(f"{args.output}.html")


if __name__ == "__main__":
    main() 